import structlog

from decimal import Decimal, InvalidOperation

from .constants import DATA_DIR, OUT_DIR
from .utils import (
    classify_crop_code,
    iter_merged_data,
    save_processed_chunk,
    get_merge_cap_data,
    get_unique_crop_codes,
)

from ...services.ecoscheme_payments.classification import get_exclusivity_land_uses
from ...services.ecoscheme_payments.main import (
    calculate_ecoscheme_payments,
    get_eligible_ecoschemes_data,
)
from ...services.sigpac_tools_v2.find import find_from_cadastral_registry
from ...utils.parcel_finder_utils import check_cadastral_data

logger = structlog.getLogger(__name__)

# Set chunk size for production streaming. Set max_rows=10 for fast testing if needed
CHUNK_SIZE = 10_000
MAX_ROWS_TEST = None  # Change to 10 or 100 for testing, None for full file


def process_cap_data(
    processed_output_file: str, merged_output_file: str, classification_file: str
):
    out_files = []
    eligible_schemes_by_land_use, non_eligible_uses = get_eligible_ecoschemes_data(
        rules_json_filepath=classification_file
    )

    out_files.append(merged_output_file)

    # 1. Quick search to inspect unique crop codes & descriptions
    get_unique_crop_codes(merged_output_file)

    # 2. Stream through merged data in chunks
    is_first_chunk = True

    for chunk in iter_merged_data(
        merged_output_file, batch_size=CHUNK_SIZE, max_rows=MAX_ROWS_TEST
    ):
        processed_entries = []
        unprocessed_entries = []
        for entry in chunk:
            # Validate LNA_CODIGO range
            lna_code = entry.get("LNA_CODIGO")
            if lna_code is None or not (500 <= int(lna_code) <= 520):
                logger.debug(f"Skipping non-ecoscheme entry: {entry}")
                processed_entries.append(entry)
                continue  # skip non-ecoscheme entries

            # Build cadastral reference
            province = str(entry.get("PRO_CODIGO", "0"))
            municipality = str(entry.get("MSP_CODIGO", "0"))
            polygon = str(entry.get("REC_POLIGONO", "0"))
            parcel_id = str(entry.get("REC_PARCELA", "0"))

            logger.debug(f"ENTRY: {entry}")

            try:
                actual_cad_ref = check_cadastral_data(
                    None,
                    province=province,
                    municipality=municipality,
                    polygon=polygon,
                    parcel_id=parcel_id,
                )
                __, metadata = find_from_cadastral_registry(actual_cad_ref)
                crop_data = metadata.get("query").pop()
            except Exception as e:
                if "No geometries found in the provided JSON data" in str(e):
                    logger.warning(str(e))
                else:
                    logger.error(e)
                logger.info("Saving entry to unprocessed entry list")
                unprocessed_entries.append(entry)

            # if not saved_file:
            #     with open(f"{actual_cad_ref}_metadata.json", "w") as f:
            #         import json
            #         json.dump(metadata, f, indent=4)
            #         logger.debug("SAVED FILE!")
            #     saved_file = True

            # Format entry
            sup_total = entry.get("SUP_TOTAL_HA", 0)
            total_parcel_area = Decimal(str(sup_total if sup_total is not None else 0))

            crop_merged_id = entry.get("PRD_CODIGO")
            crop_merged_desc = entry.get("PRD_DESC")

            parsed_data = {
                crop_data.get(
                    "uso_sigpac", classify_crop_code(crop_merged_id, crop_merged_desc)
                ): {
                    "area": total_parcel_area,
                    "irrigation_coef": str(crop_data.get("coef_regadio") or "0.0")
                    + "%",
                    "slope_coef": str(crop_data.get("pendiente_media") or "0.0") + "%",
                }
            }

            land_use_assignments = get_exclusivity_land_uses(
                eligible_schemes_by_land_use, non_eligible_uses, parsed_data
            )

            (
                estimated_payments,
                __,
                __,
                __,
            ) = calculate_ecoscheme_payments(parsed_data, land_use_assignments)

            updated_entry = dict(entry)
            updated_entry["%_PENDIENTE_MEDIA"] = str(
                crop_data.get("pendiente_media", "0.0")
            )

            if estimated_payments:
                scheme_data = estimated_payments[0]
                scheme_key = f"{scheme_data.get('Ecoscheme_ID', '')}: {scheme_data.get('Ecoscheme_Name', '')}"
                updated_entry["ECORREGIMEN_CODIGO"] = scheme_key

                is_pluri = scheme_data.get("pluriannuality_applicable", False)
                pluri_factor = Decimal("1.25") if is_pluri else Decimal("1.00")

                for rate_type in ["Peninsular", "Insular"]:
                    rate_info = scheme_data.get(rate_type, 0.0)

                    # Extract numerical value safely
                    if isinstance(rate_info, dict):
                        raw_val = rate_info.get("Total_Base_Payment_EUR", 0.0)
                    else:
                        raw_val = rate_info

                    # Convert to Decimal safely
                    try:
                        if raw_val is None:
                            base_payment = Decimal("0.0")
                        else:
                            base_payment = Decimal(str(raw_val))
                    except (InvalidOperation, TypeError, ValueError):
                        base_payment = Decimal("0.0")

                    logger.debug(f"base_payment:\t{base_payment} for {rate_type}")
                    pluri_payment = base_payment * pluri_factor

                    prefix = rate_type.upper()
                    updated_entry[f"{prefix}_PAGO_BASE"] = float(base_payment)
                    updated_entry[f"{prefix}_PAGO_PLURI"] = float(pluri_payment)
            else:
                updated_entry["ECORREGIMEN_CODIGO"] = ""
                updated_entry["PENINSULAR_PAGO_BASE"] = 0.0
                updated_entry["PENINSULAR_PAGO_PLURI"] = 0.0
                updated_entry["INSULAR_PAGO_BASE"] = 0.0
                updated_entry["INSULAR_PAGO_PLURI"] = 0.0
            processed_entries.append(updated_entry)

        # 3. Append chunk results incrementally to output file
        save_processed_chunk(
            processed_entries, processed_output_file, is_first_chunk=is_first_chunk
        )
        is_first_chunk = False
    return unprocessed_entries if len(unprocessed_entries) > 0 else None


if __name__ == "__main__":
    years = [2023, 2024]
    OUT_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)
    for year in years:
        merged_output_file = str(OUT_DIR / f"PAC_{year}_MERGED.csv")
        processed_output_file = str(OUT_DIR / f"PAC_{year}_PROCESSED.csv")
        classification_file = str(DATA_DIR / f"classification_{year}.json")

        merged_output_file = get_merge_cap_data(year, output_file=merged_output_file)
        process_cap_data(
            processed_output_file=processed_output_file,
            merged_output_file=merged_output_file,
            classification_file=classification_file,
        )
