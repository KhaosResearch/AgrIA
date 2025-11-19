
from decimal import Decimal, ROUND_HALF_UP

from .constants import PLURIANNUALITY_BONUS_PER_HA, ROUNDING_PAYMENT, ROUNDING_RATE

def is_valid_rate_for_coefficients(scheme_id, subtype, slope, irrigation):
    """
    Validate if an ecoscheme is compatible with the slope or irrigation coefficients.
    Returns True if valid, False otherwise.
    """
    slope_kw = {
        "flat": ["Flat Woody Crops", "Terrenos Llanos"],
        "medium": ["Medium Slope", "Pendiente Media"],
        "steep": ["Steep Slope", "Pendiente Elevada", "Terraces", "Balcanes"],
    }
    irrig_kw = {
        "irrigated": ["Irrigated", "Regadío"],
        "humid": ["Rainfed Humid", "Húmedo"],
        "rainfed": ["Rainfed", "Secano"],
    }

    # --- P6 / P7 schemes: depend on slope ---
    if any(k in scheme_id for k in ("P6", "P7")):
        if slope > 12:
            return any(k in subtype for k in slope_kw["steep"])
        elif 6 < slope <= 12:
            return any(k in subtype for k in slope_kw["medium"])
        else:  # slope <= 6
            return any(k in subtype for k in slope_kw["flat"])

    # --- P3 / P4 schemes: depend on irrigation ---
    elif any(k in scheme_id for k in ("P3", "P4")):
        if irrigation > 50:
            return any(k in subtype for k in irrig_kw["irrigated"])
        elif 25 < irrigation <= 50:
            return any(k in subtype for k in irrig_kw["humid"])
        else:  # irrigation <= 20
            return any(k in subtype for k in irrig_kw["rainfed"])

    # Other schemes: no restriction
    return True

def calculate_payments_for_rate_type(area: Decimal, rate_details: dict, pluri_applicable: bool) -> dict:
    """Calculates Base and Pluriannuality payments for a single area type (Peninsular or Insular)."""
    
    current_rate = Decimal('0.0')
    applied_tier = "N/A"
    
    if 'Flat' in rate_details:
        # Flat Rate
        current_rate = rate_details['Flat']
        applied_tier = "Flat Rate"
    else:
        # Tiered Rate
        L = rate_details['Threshold_ha']
        if L is not None and area <= L:
            current_rate = rate_details['Tier_1']
            applied_tier = "Tier 1"
        else:
            current_rate = rate_details['Tier_2']
            applied_tier = "Tier 2"

    # Payments
    current_rate = current_rate if "/" not in str(current_rate) else Decimal(str("0"))
    base_payment = area * current_rate
    payment_with_pluri = base_payment

    if pluri_applicable:
        payment_with_pluri = area * (current_rate + PLURIANNUALITY_BONUS_PER_HA)
    
    payment_with_pluri = Decimal(str(payment_with_pluri))
    current_rate = Decimal(str(current_rate))
    base_payment = Decimal(str(base_payment))
    
    return {
        "Applied_Base_Payment_EUR": float(current_rate.quantize(ROUNDING_RATE, rounding=ROUND_HALF_UP)),
        "Total_Base_Payment_EUR": float(base_payment.quantize(ROUNDING_PAYMENT, rounding=ROUND_HALF_UP)),
        "Total_with_Pluriannuality_EUR": float(payment_with_pluri.quantize(ROUNDING_PAYMENT, rounding=ROUND_HALF_UP)),
        "Applicable": f"Yes ({applied_tier} Applied)" if applied_tier != "Flat Rate" else "Yes (Flat Rate)"
    }
