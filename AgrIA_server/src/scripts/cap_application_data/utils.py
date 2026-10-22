import duckdb
import structlog

import pandas as pd

from typing import Generator, List, Dict, Any, Optional

from .constants import DATA_DIR

from ...config.constants import ASSETS_DIR

logger = structlog.get_logger()


def get_merge_cap_data(year, output_file=None):
    ayudas_file = ASSETS_DIR / "data" / f"PAC_{year}_AYUDAS.csv"
    superficies_file = ASSETS_DIR / "data" / f"PAC_{year}_SUPERFICIES.csv"
    output_file = output_file if output_file else f"PAC_{year}_MERGED.csv"

    logger.debug(f"Processing {year}...")

    con = duckdb.connect()

    query = f"""
    COPY (
        SELECT
            a.*,
            s.* EXCLUDE (SECUENCIAL, REC_CODIGO)
        FROM read_csv_auto('{ayudas_file}', header=True) AS a
        LEFT JOIN read_csv_auto('{superficies_file}', header=True) AS s
            ON a.SECUENCIAL = s.SECUENCIAL
            AND a.REC_CODIGO = s.REC_CODIGO
    )
    TO '{output_file}'
    (HEADER, DELIMITER ',');
    """

    con.execute(query)
    con.close()

    logger.debug(f"Finished: {output_file}")
    return output_file


def generate_crop_codes_report(
    merged_file: str,
    code_key: str = "PRD_CODIGO",
    desc_key: str = "PRD_DESC",
    report_output_csv: str = str(DATA_DIR / "crop_codes_report.csv"),
):
    """
    Scans the merged CAP CSV file and generates a complete summary report of all unique
    `code_key` and `desc_key` pairs along with their occurrence count.
    """
    con = duckdb.connect()

    # NOTE: Removed trailing semicolon from query string so it works cleanly inside COPY(...)
    query = f"""
        SELECT 
            {code_key}, 
            {desc_key}, 
            COUNT(*) AS total_occurrences
        FROM read_csv_auto('{merged_file}', header=True)
        GROUP BY {code_key}, {desc_key}
        ORDER BY TRY_CAST({code_key} AS INT) ASC, {code_key} ASC
    """

    results = con.execute(query).fetchall()

    # Export query results directly to CSV
    export_query = f"""
        COPY ({query}) 
        TO '{report_output_csv}' 
        (HEADER, DELIMITER ',');
    """
    con.execute(export_query)
    con.close()

    # Display report in console
    print(f"\n{'=' * 70}")
    print(f" UNIQUE {code_key} & {desc_key} REPORT: {merged_file}")
    print(f"{'=' * 70}")
    print(f"{f'{code_key}':<15} | {'COUNT':<10} | {f'{desc_key}'}")
    print(f"{'-' * 70}")

    for code, desc, count in results:
        print(f"{str(code):<15} | {count:<10} | {desc}")

    print(f"{'-' * 70}")
    print(f"Total Unique Pairs Found: {len(results)}")
    print(f"Full report exported to: {report_output_csv}\n")

    return results


def get_unique_crop_codes(merged_file: str):
    """
    Quick search method using DuckDB to retrieve unique (PRD_CODIGO, PRD_DESC) pairs.
    """
    con = duckdb.connect()
    query = f"""
        SELECT DISTINCT PRD_CODIGO, PRD_DESC 
        FROM read_csv_auto('{merged_file}', header=True)
        ORDER BY PRD_CODIGO
    """
    results = con.execute(query).fetchall()
    con.close()

    logger.debug(
        f"\n--- Found {len(results)} Unique PRD_CODIGO / PRD_DESC pairs in {merged_file} ---"
    )
    for code, desc in results[:20]:  # Show first 20 as sample
        print(f"PRD_CODIGO: {code} -> PRD_DESC: {desc}")
    return results


def classify_crop_code(code: float, desc: str) -> str:
    if pd.isna(code) or pd.isna(desc):
        return "UNKNOWN"

    desc_upper = str(desc).strip().upper()

    # 1. Exact Subtype/Mixed Associations
    mixed_map = {
        "VIÑA - OLIVAR": "VO",
        "VIÑA - FRUTAL": "VF",
        "OLIVAR - FRUTAL": "OF",
        "CEREZO-OLIVAR": "OF",
        "NARANJO-AGUACATE": "CF",
        "NARANJO-CAQUI": "CF",
        "CEREZO-ALGARROBO": "FF",
        "ALMENDRO-OLIVAR": "FL",
        "NARANJO-MANDARINO": "CI",
    }
    if desc_upper in mixed_map:
        return mixed_map[desc_upper]

    # 2. Direct Monoculture Matches
    if desc_upper == "OLIVO":
        return "OV"
    if desc_upper == "VIÑA":
        return "VI"
    if desc_upper == "HUERTA":
        return "TH"
    if desc_upper == "PASTOS PERMANENTES DE 5 O MÁS AÑOS":
        return "PS"

    # 3. Citrus Family (CI)
    citrus_set = {
        "CLEMENTINA",
        "SATSUMA",
        "NARANJO",
        "LIMONERO",
        "POMELO O TORONJA",
        "MANDARINO",
        "MANDARINO HÍBRIDO",
        "NARANJO AMARGO",
        "KUMQUAT",
        "LIMEQUAT",
        "MANO DE BUDA",
        "CAVIAR CÍTRICO/ FINGER LIME",
        "LIMA",
    }
    if desc_upper in citrus_set:
        return "CI"

    # 4. Nut Trees / Frutos Secos (FS)
    nuts_set = {
        "ALMENDRO",
        "NOGAL",
        "CASTAÑO",
        "ALGARROBO",
        "AVELLANO",
        "PISTACHO",
        "FRUTOS DE CÁSCARA",
    }
    if desc_upper in nuts_set:
        return "FS"

    # 5. Permanent Fruit Trees (FY)
    fruit_set = {
        "MELOCOTONERO",
        "NECTARINO",
        "ALBARICOQUERO",
        "PERAL",
        "MANZANO",
        "CEREZO",
        "CIRUELO",
        "OTROS FRUTALES",
        "ZARZAMORA",
        "FRAMBUESA",
        "PLATERINA",
        "PARAGUAYO",
        "ENDRINO O ARAÑÓN",
        "MEMBRILLO",
        "KIWI",
        "CAQUI O PALOSANTO",
        "NÍSPERO",
        "GROSELLERO",
        "ARÁNDANO",
        "GRANADO",
        "HIGUERA",
        "OPUNTIA",
        "FRUTOS DEL BOSQUE",
        "AGUACATE",
        "MANGO",
        "CHIRIMOYO",
        "PAPAYA",
        "MORERA",
        "BAYAS DE GOJI",
        "AZUFAIFO",
        "LITCHI",
        "ARGÁN",
        "PITAYA",
        "GUAYABO",
        "ZAPOTE",
        "PHYSALIS",
        "PALMERA DATILERA",
        "MARACUYÁ O FRUTO DE LA PASIÓN",
        "CABECERA DE CULTIVO PERMANENTE",
        "ESPECIES AROMÁTICAS LEÑOSAS",
    }
    if desc_upper in fruit_set:
        return "FY"

    # 6. Forestry / Forestal (FO)
    forestry_set = {
        "CHOPO",
        "ENCINA",
        "PAULONIA",
        "EUCALIPTO",
        "SAUCE",
        "MEZCLA DE FORESTALES",
        "TRUFA",
    }
    if desc_upper in forestry_set:
        return "FO"

    # 7. Default for Annual Crops, Vegetables, Grasses, Fallows
    return "TA"


def get_crop_sigpac_id(crop_merged_id: int | str) -> str:
    """
    Maps the crop merged ID (PRD_CODIGO) to the corresponding SIGPAC ID.
    Using reference mapping from crop_classification_es.
    """
    if crop_merged_id is None:
        return "TA"

    crop_str = str(crop_merged_id).strip().upper()

    mapping = {
        "101": "OV",  # Olivar
        "102": "VI",  # Viñedo
        "103": "TA",  # Tierra arable
        "104": "PA",  # Pastos
        "105": "FO",  # Forestal
        "106": "CS",  # Cítricos
        "107": "FY",  # Frutal
        "108": "TH",  # Huerta
        "109": "IV",  # Invernaderos
        "2": "CA",  # Viales
        "3": "CE",  # Cítricos
        "4": "FY",  # Frutal
        "5": "TH",  # Huerta
        "6": "LE",  # Leguminosas / TA
        "7": "MA",  # Maíz / TA
        "8": "PA",  # Pastos
        "9": "TO",  # Tomate / TA
        "10": "VI",  # Viñedo
    }

    valid_sigpac_classes = {
        "AG",
        "CA",
        "CF",
        "CI",
        "CS",
        "CV",
        "ED",
        "EP",
        "FF",
        "FL",
        "FO",
        "FS",
        "FV",
        "FY",
        "IM",
        "IV",
        "OC",
        "OF",
        "OV",
        "PA",
        "PR",
        "PS",
        "TA",
        "TH",
        "VF",
        "VI",
        "VO",
        "ZC",
        "ZU",
        "ZV",
    }

    if crop_str in valid_sigpac_classes:
        return crop_str

    return mapping.get(crop_str, "TA")


def iter_merged_data(
    merged_file: str, batch_size: int = 10_000, max_rows: Optional[int] = None
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Streams records from the merged CSV in chunks using DuckDB.

    :param merged_file: Path to input CSV.
    :param batch_size: Number of records per chunk yielded.
    :param max_rows: Optional limit on total rows to read (useful for testing/demo).
    """
    con = duckdb.connect()
    limit_clause = f"LIMIT {max_rows}" if max_rows is not None else ""

    query = f"""
        SELECT * 
        FROM read_csv_auto('{merged_file}', header=True)
        {limit_clause}
    """

    arrow_reader = con.execute(query).fetch_record_batch(batch_size)
    try:
        for batch in arrow_reader:
            yield batch.to_pylist()
    finally:
        con.close()


def save_processed_chunk(
    processed_entries: List[Dict[str, Any]],
    output_file: str,
    is_first_chunk: bool = False,
):
    """
    Appends a list of processed dictionaries to the output CSV file.
    """
    if not processed_entries:
        return

    df = pd.DataFrame(processed_entries)
    mode = "w" if is_first_chunk else "a"
    header = is_first_chunk
    df.to_csv(output_file, mode=mode, header=header, index=False)


def save_processed_results(processed_records: list[dict], output_file: str):
    """
    Saves processed results containing new calculated fields into a separate CSV file.
    """
    df = pd.DataFrame(processed_records)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved processed results to: {output_file}")
