from decimal import Decimal

from server.services.ecoscheme_payments.utils import calculate_payments_for_rate_type, is_valid_rate_for_coefficients
from server.services.ecoscheme_payments.constants import PLURIANNUALITY_BONUS_PER_HA, ROUNDING_PAYMENT

# --- Test Coefficient Validation ---


def test_valid_rate_for_slope_p6_steep():
    """Test P6 scheme for steep slope criteria (slope > 12)."""
    # 15% slope, 'Steep Slope Woody Crops' subtype
    assert is_valid_rate_for_coefficients(
        "P6/P7", "Steep Slope Woody Crops", 15.0, 0.0) is True
    # 15% slope, 'Flat Woody Crops' subtype (should fail)
    assert is_valid_rate_for_coefficients(
        "P6/P7", "Flat Woody Crops", 15.0, 0.0) is False


def test_valid_rate_for_slope_p6_flat():
    """Test P6 scheme for flat slope criteria (slope <= 6)."""
    # 5% slope, 'Flat Woody Crops' subtype
    assert is_valid_rate_for_coefficients(
        "P6/P7", "Flat Woody Crops", 5.0, 0.0) is True
    # 5% slope, 'Steep Slope Woody Crops' subtype (should fail)
    assert is_valid_rate_for_coefficients(
        "P6/P7", "Steep Slope Woody Crops", 5.0, 0.0) is False


def test_valid_rate_for_irrigation_p3_irrigated():
    """Test P3 scheme for irrigated criteria (irrigation > 50)."""
    # 80% irrigation, 'Irrigated' subtype
    assert is_valid_rate_for_coefficients(
        "P3/P4", "Irrigated", 0.0, 80.0) is True
    # 80% irrigation, 'Rainfed' subtype (should fail)
    assert is_valid_rate_for_coefficients(
        "P3/P4", "Rainfed", 0.0, 80.0) is False


def test_valid_rate_for_non_restricted_scheme():
    """Test a scheme not tied to slope/irrigation (e.g., P1)."""
    assert is_valid_rate_for_coefficients(
        "P1", "Mediterranean Pastures", 0.0, 78.0) is True


# --- Test Payment Calculations ---

def test_calculate_tiered_tier1_payment():
    """Test Tier 1 payment (area <= threshold) without pluriannuality."""
    area = Decimal('20.0')
    rate_details = {'Tier_1': Decimal('100.0'), 'Tier_2': Decimal(
        '60.0'), 'Threshold_ha': Decimal('30.0')}

    results = calculate_payments_for_rate_type(area, rate_details, False)

    expected_base = area * rate_details['Tier_1']
    assert results['Applied_Base_Payment_EUR'] == 100.0
    assert results['Total_Base_Payment_EUR'] == float(
        expected_base.quantize(ROUNDING_PAYMENT))
    assert results['Total_with_Pluriannuality_EUR'] == float(
        expected_base.quantize(ROUNDING_PAYMENT))
    assert results['Applicable'] == "Yes (Tier 1 Applied)"


def test_calculate_flat_payment_with_pluriannuality():
    """Test Flat Rate payment with pluriannuality bonus."""
    area = Decimal('10.0')
    flat_rate = Decimal('350.0')
    rate_details = {'Flat': flat_rate}

    results = calculate_payments_for_rate_type(area, rate_details, True)

    expected_rate = flat_rate + PLURIANNUALITY_BONUS_PER_HA
    expected_total = area * expected_rate

    assert results['Applied_Base_Payment_EUR'] == 350.0
    assert results['Total_Base_Payment_EUR'] == float(
        (area * flat_rate).quantize(ROUNDING_PAYMENT))
    assert results['Total_with_Pluriannuality_EUR'] == float(
        expected_total.quantize(ROUNDING_PAYMENT))
    assert results['Applicable'] == "Yes (Flat Rate)"
