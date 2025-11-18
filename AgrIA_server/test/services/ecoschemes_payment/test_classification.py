from decimal import Decimal
from server.services.ecoscheme_payments.classification import (
    get_exclusivity_land_uses,
    get_ecoschemes_rates_and_totals
)
from server.services.ecoscheme_payments.main import calculate_ecoscheme_payment
from server.services.ecoscheme_payments.rules import get_ecoscheme_rules_data

# Use mocks to isolate the main function from file IO for testing
def test_exclusivity_rule_assignment(parsed_data_fixture, dummy_rules_data):
    """
    Test the assignment of the best scheme based on payment/ha and coefficient compatibility.
    
    """
    eligible, non_eligible = get_ecoscheme_rules_data(dummy_rules_data)
    assignments = get_exclusivity_land_uses(eligible, non_eligible, parsed_data_fixture)

    # 1. MT, PA, PR, PS are assigned to P1 (Mediterranean Pastures)
    
    # Check one of the P1 assignments (e.g., MT)
    assert assignments['MT']['id'] == 'P1'
    # Peninsular Tier 1 Rate: 27.27
    assert assignments['MT']['payment_per_ha_total'] == Decimal('49.27') 
    
    # 2. Check P6/P7 (VI, FY) assignment.
    # VI area (9.3441ha) < Threshold (15.0ha) -> Tier 1 (59.12/ha) + Pluriannuality (25.0) = 84.12/ha
    assert assignments['VI']['id'] == 'P6/P7'
    assert assignments['VI']['payment_per_ha_total'] == Decimal('124.12') 

    # 3. Check TA assignment. P3/P4 Irrigated Tier 1 (141.742439/ha) + Pluri (25.0) = 166.742439/ha
    assert assignments['TA']['id'] == 'P3/P4'
    assert assignments['TA']['payment_per_ha_total'] == Decimal('246.742439')

    # 4. Check Non-Eligible (e.g., IM)
    assert assignments['IM']['name'] == 'Non-Eligible'

def test_ecoschemes_rates_and_totals_grouping(parsed_data_fixture, dummy_rules_data):
    """Test that assignments are correctly grouped and areas summed."""
    
    eligible, non_eligible = get_ecoscheme_rules_data(dummy_rules_data)
    assignments = get_exclusivity_land_uses(eligible, non_eligible, parsed_data_fixture)

    results = get_ecoschemes_rates_and_totals(parsed_data_fixture, assignments)

    # Check 5 total groups
    assert len(results) == 5
    
    # Check P1 Grouping (PA, PS, PR, MT)
    p1_med = results['P1_Mediterranean Pastures']
    assert p1_med['Total_Area_ha'] == Decimal('7.0703') # PA + PS + PR + MT
    assert p1_med['Land_Uses'] == ['PA', 'PS', 'PR', 'MT']
    
    # Check P3/P4 Grouping (TA)
    p3p4_med = results['P3/P4_Irrigated']
    assert p3p4_med['Total_Area_ha'] == Decimal('22.7474') # TA
    assert 'TA' in p3p4_med['Land_Uses']
    
    # Check P5 (B) Grouping (AG)
    p5b_med = results['P5(B)_Under Water']
    assert p5b_med['Total_Area_ha'] == Decimal('0.4099') # AG
    assert 'AG' in p5b_med['Land_Uses']

    # Check P6/P7 Grouping (VI and FY)
    p6p7_flat = results['P6/P7_Flat Woody Crops']
    assert p6p7_flat['Total_Area_ha'] == Decimal('9.4863') # VI + FY
    assert sorted(p6p7_flat['Land_Uses']) == ['FY', 'VI']

    # Check Non-Eligible
    non_eligible_res = results['Non-Eligible'] # Assuming Subtype is None
    assert non_eligible_res['Total_Area_ha'] == Decimal('6.0193') # FO + CA + IM + ED + ZU
    assert sorted(non_eligible_res['Land_Uses']) == ['CA', 'ED', 'FO', 'IM', 'ZU']

def test_main_calculation_output(sample_input_data_str, mocker):
    """
    End-to-end test of the main function, mocking the rule loading.
    """
    mocker.patch('server.benchmark.vlm.constants.OG_CLASSIFICATION_FILEPATH', 'dummy_path.json')
    
    output = calculate_ecoscheme_payment(sample_input_data_str)
    
    # Check Final Summary
    assert output['Total_Parcel_Area_ha'] == 45.7332
    assert output['Final_Results']['Total_Aid_without_Pluriannuality_EUR'] == 4037.39
    assert output['Final_Results']['Total_Aid_with_Pluriannuality_EUR'] == 4843.24

    ecoschemes_total_payments = [('P1', 192.81, 192.81), ('P3/P4', 3224.27, 3792.96), ('P5 (B)', 59.48, 59.48), ('P6/P7', 560.83, 797.99), ('N/A', 'N/A', 'N/A')]

    for ecoscheme_id, total_base_payment, total_pluri_payment in ecoschemes_total_payments:
        # Check Detailed Payments for all ecoschemes
        payment = [p for p in output['Estimated_Total_Payment'] if p['Ecoscheme_ID'] == ecoscheme_id][0]

        # Peninsular (Used for Summary)
        assert payment['Peninsular']['Total_Base_Payment_EUR'] == total_base_payment 
        assert payment['Peninsular']['Total_with_Pluriannuality_EUR'] == total_pluri_payment