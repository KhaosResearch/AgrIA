import re
import json
import structlog
from decimal import Decimal, ROUND_HALF_UP

from .classification import get_ecoschemes_rates_and_totals, get_exclusivity_land_uses
from .rules import get_ecoscheme_rules_data
from .utils import calculate_payments_for_rate_type

from .constants import ROUNDING_AREA, ROUNDING_PAYMENT

from ...benchmark.vlm.constants import LANG, OG_CLASSIFICATION_FILEPATH


logger = structlog.get_logger()

# --- Main Calculation Function (Modified) ---


def calculate_ecoscheme_payment(input_data_str: str, lang: str = LANG, rules_json_filepath: str = OG_CLASSIFICATION_FILEPATH) -> dict:
    """
    Processes land use input data and calculates estimated Eco-scheme payments
    by applying the Critical Exclusivity Rule (choosing the highest payment/ha
    across all rate types) and including both Peninsular and Insular calculations.
    """

    # --- 1. PREPARE RULES AND CONSTANTS ---
    with open(rules_json_filepath, 'r') as file:
        all_rules_list = json.load(file)
    rules_json_str = json.dumps(all_rules_list[lang.upper()])

    try:
        rules_data_list = json.loads(rules_json_str.strip())
    except json.JSONDecodeError:
        # Fallback for non-list JSON string (often means str(dict) was passed)
        rules_data_list = json.loads(f'[{rules_json_str.strip()}]')

    eligible_schemes_by_land_use, non_eligible_uses = get_ecoscheme_rules_data(
        rules_data_list)

    # --- 2. PARSE INPUT DATA AND CALCULATE TOTAL AREA ---

    land_use_regex = {
        "en": r'- Land Use: ([A-Z]{2})\s*- Eligible surface \(ha\): ([\d\.]+)\s*- Irrigation Coeficient: ([\d\.]+%)\s*(?:- Slope Coeficient: ([\d\.]+%))?',
        "es": r'- Tipo de Uso:\s*([A-Z]{2})\s*- Superficie admisible \(ha\):\s*([\d\.]+)\s*- Coef\. de Regadío:\s*([\d\.]+%)\s*(?:- Pendiente media:\s*([\d\.]+%))?'
    }
    land_use_blocks = re.findall(
        land_use_regex[lang.lower()], input_data_str, re.DOTALL)

    parsed_data = {}
    total_parcel_area = Decimal('0.0')

    for match in land_use_blocks:
        land_use_code, area_str, irrigation_coef, slope_coef = match
        area = Decimal(area_str)
        total_parcel_area += area
        parsed_data[land_use_code] = {
            "area": area, "irrigation_coef": irrigation_coef, "slope_coef": slope_coef}

    # --- 3. APPLY EXCLUSIVITY RULE (Determine best ES/ha for each LU) ---

    land_use_assignments = get_exclusivity_land_uses(
        eligible_schemes_by_land_use, non_eligible_uses, parsed_data)

    # --- 4. GROUP RESULTS AND CALCULATE TOTAL PAYMENTS ---

    final_scheme_results = get_ecoschemes_rates_and_totals(
        parsed_data, land_use_assignments)

    estimated_payments = []
    total_aid_no_pluriannuality = Decimal('0.0')
    total_aid_with_pluriannuality = Decimal('0.0')
    pluri_area = Decimal('0.0')
    applicable_ecoschemes = []

    sorted_keys = sorted(
        [k for k in final_scheme_results.keys() if k != 'Non-Eligible'])
    if 'Non-Eligible' in final_scheme_results:
        sorted_keys.append('Non-Eligible')

# Process final payments for each group
    # logger.debug(f"eligible_schemes_by_land_use\t{eligible_schemes_by_land_use}")
    for key in sorted_keys:
        res = final_scheme_results[key]
        area = res["Total_Area_ha"]

        if key == 'Non-Eligible':
            land_use_list = sorted(res["Land_Uses"])
            non_eligible_input_land_uses = [
                land_use for land_use in land_use_list if land_use in parsed_data]

            estimated_payments.append({
                "Ecoscheme_ID": res["Ecoscheme_ID"], "Ecoscheme_Name": res["Ecoscheme_Name"], "Ecoscheme_Subtype": res["Ecoscheme_Subtype"],
                "Land_Use_Class_Eligible": ", ".join(non_eligible_input_land_uses),
                "Total_Area_ha": float(area.quantize(ROUNDING_AREA, rounding=ROUND_HALF_UP)),
                # Peninsular and Insular data kept for completeness, but set to N/A for Non-Eligible
                "Peninsular": {"Applied_Base_Payment_EUR": "N/A", "Total_Base_Payment_EUR": "N/A", "Total_with_Pluriannuality_EUR": "N/A", "Applicable": "N/A"},
                "Insular": {"Applied_Base_Payment_EUR": "N/A", "Total_Base_Payment_EUR": "N/A", "Total_with_Pluriannuality_EUR": "N/A", "Applicable": "N/A"},
            })
        else:
            # Calculate BOTH Peninsular and Insular payments
            # Note: The chosen scheme was already determined using Peninsular rates in Section 3.
            peninsular_results = calculate_payments_for_rate_type(
                area, res['rates']['Peninsular'], res['pluriannuality_applicable'])
            insular_results = calculate_payments_for_rate_type(
                area, res['rates']['Insular'], res['pluriannuality_applicable'])

            # --- SUMMING FOR FINAL REPORT: USE PENINSULAR RATES ONLY ---
            applied_base_payment_for_summary = Decimal(
                peninsular_results['Total_Base_Payment_EUR'])
            applied_total_payment_for_summary = Decimal(
                peninsular_results['Total_with_Pluriannuality_EUR'])

            total_aid_no_pluriannuality += applied_base_payment_for_summary
            total_aid_with_pluriannuality += applied_total_payment_for_summary

            if res['pluriannuality_applicable']:
                pluri_area += area

            applicable_ecoschemes.append(res["Ecoscheme_ID"])

            # Format the eligible Land Use string
            land_use_list_only = ", ".join(sorted(res['Land_Uses']))
            land_use_area_total = area.quantize(
                ROUNDING_PAYMENT, rounding=ROUND_HALF_UP)
            land_use_eligible_str = f"{land_use_list_only} ({land_use_area_total} ha)"

            # Append to payments list with nested results
            estimated_payments.append({
                "Ecoscheme_ID": res["Ecoscheme_ID"],
                "Ecoscheme_Name": res["Ecoscheme_Name"],
                "Ecoscheme_Subtype": res["Ecoscheme_Subtype"],
                "Land_Use_Class_Eligible": land_use_eligible_str,
                "Total_Area_ha": float(area.quantize(ROUNDING_AREA, rounding=ROUND_HALF_UP)),
                "Peninsular": peninsular_results,
                "Insular": insular_results,
            })

    # -------------------------------------------------------------
    # --- 5. FINAL RESULTS SUMMARY (Reporting Peninsular Only) ---
    # -------------------------------------------------------------

    final_results = {
        "Applicable_Ecoschemes": sorted(list(set(applicable_ecoschemes))),
        "Total_Aid_without_Pluriannuality_EUR": float(total_aid_no_pluriannuality.quantize(ROUNDING_PAYMENT, rounding=ROUND_HALF_UP)),
        "Total_Aid_with_Pluriannuality_EUR": float(total_aid_with_pluriannuality.quantize(ROUNDING_PAYMENT, rounding=ROUND_HALF_UP))
        # "Clarifications": clarifications
    }

    # Final Output Structure - Update Context
    output_dict = {
        "Report_Type": "EcoScheme_Payment_Estimate",
        "Total_Parcel_Area_ha": float(total_parcel_area.quantize(ROUNDING_AREA, rounding=ROUND_HALF_UP)),
        "Calculation_Context": {
            "Rate_Applied": "Peninsular_Rates_Used_For_Final_Summary_Total",  # Updated context
            "Source": "Provisional base rates for Eco-schemes, 2025 CAP Campaign"
        },
        "Estimated_Total_Payment": estimated_payments,
        "Final_Results": final_results
    }

    return output_dict
