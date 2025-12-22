import structlog

from decimal import Decimal

from .constants import PLURIANNUALITY_BONUS_PER_HA
from .utils import is_valid_rate_for_coefficients

logger = structlog.get_logger()


def get_exclusivity_land_uses(eligible_schemes_by_land_use, non_eligible_uses, parsed_data, lang="EN") -> dict:
    land_use_assignments = {}

    for land_use_code, data in parsed_data.items():
        area = data.get('area', 0.0)
        irrigation = float(data.get('irrigation_coef', 0.0)
                           [:-1])  # Input format '00.00%'
        slope = float(data.get('slope_coef')[
                      :-1]) if len(data.get('slope_coef')) > 0 else 0.0  # Input format '00.00%'

        # Skip non-eligible uses
        if land_use_code in non_eligible_uses or land_use_code not in eligible_schemes_by_land_use:
            land_use_assignments[land_use_code] = {
                'id': 'N/A',
                'name': 'Non-Eligible',
                'subtype': None,
                'payment_per_ha': Decimal('0')
            }
            continue

        best_payment_per_ha = Decimal('-1')
        best_scheme_assignment = None

        for rate_type in ["Peninsular", "Insular"]:
            for scheme in eligible_schemes_by_land_use[land_use_code]:
                scheme_id = scheme["id"]
                scheme_subtype = scheme["subtype"]

                # Check irrigation and slope coefficient for better assignment accuracy
                if not is_valid_rate_for_coefficients(scheme_id, scheme_subtype, slope, irrigation):
                    continue

                # Get rate details
                rate_details = scheme['rates'].get(rate_type)
                if not rate_details:
                    continue

                # Determine base rate
                if 'Flat' in rate_details:
                    current_rate = Decimal(
                        rate_details['Flat']) if rate_details['Flat'] != "N/A" else Decimal("0")
                else:
                    threshold = rate_details.get('Threshold_ha')
                    tier1 = Decimal(rate_details.get('Tier_1', 0))
                    tier2 = Decimal(rate_details.get('Tier_2', 0))
                    current_rate = tier1 if (
                        threshold and area <= threshold) else tier2

                # Add pluriannuality if applicable
                payment_per_ha_total = current_rate
                if scheme.get('pluriannuality_applicable'):
                    payment_per_ha_total += PLURIANNUALITY_BONUS_PER_HA

                # Validate value and assign if better
                if payment_per_ha_total > best_payment_per_ha:
                    best_payment_per_ha = payment_per_ha_total
                    best_scheme_assignment = scheme.copy()
                    best_scheme_assignment['best_rate_type'] = rate_type
                    best_scheme_assignment['payment_per_ha_total'] = payment_per_ha_total

        # Store final best result
        if best_scheme_assignment:
            land_use_assignments[land_use_code] = best_scheme_assignment
        else:
            land_use_assignments[land_use_code] = {
                'id': 'N/A',
                'name': 'Non-Eligible',
                'subtype': None,
                'payment_per_ha': Decimal('0')
            }

    return land_use_assignments


def get_ecoschemes_rates_and_totals(parsed_data, land_use_assignments) -> dict:
    final_scheme_results = {}

    for land_use_code, assignment in land_use_assignments.items():
        scheme_id = assignment.get('id', 'N/A')
        area = parsed_data[land_use_code]['area']

        scheme_key = f"{scheme_id}_{assignment['subtype']}" if scheme_id != 'N/A' else 'Non-Eligible'

        if scheme_key not in final_scheme_results:
            if scheme_key == 'Non-Eligible':
                final_scheme_results[scheme_key] = {
                    "Ecoscheme_ID": "N/A", "Ecoscheme_Name": "Non-Eligible", "Ecoscheme_Subtype": None,
                    "Total_Area_ha": Decimal('0.0'), "Land_Uses": [],
                    "Total_Base_Payment_Peninsular": Decimal('0.0'), "Total_Base_Payment_Insular": Decimal('0.0'),
                }
            else:
                final_scheme_results[scheme_key] = {
                    "Ecoscheme_ID": assignment['id'],
                    "Ecoscheme_Name": assignment['name'],
                    "Ecoscheme_Subtype": assignment['subtype'],
                    "Total_Area_ha": Decimal('0.0'),
                    "Land_Uses": [],
                    "rates": assignment['rates'],  # Full rates dictionary
                    "pluriannuality_applicable": assignment['pluriannuality_applicable'],
                    "Total_Base_Payment_Peninsular": Decimal('0.0'),
                    "Total_Base_Payment_Insular": Decimal('0.0'),
                }

        final_scheme_results[scheme_key]["Total_Area_ha"] += area
        final_scheme_results[scheme_key]["Land_Uses"].append(land_use_code)
    return final_scheme_results
