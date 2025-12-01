from decimal import Decimal

from server.services.ecoscheme_payments.rules import get_ecoscheme_rules_data


def test_get_ecoscheme_rules_data_structure(dummy_rules_data):
    """Test that the rule parser correctly structures rules by land use and extracts metadata."""

    # Simulate the rules being loaded as a JSON string and parsed
    rules_data_list = dummy_rules_data

    eligible, non_eligible = get_ecoscheme_rules_data(rules_data_list)

    # Check Non-Eligible Uses
    assert {'FO', 'CA', 'IM', 'ED', 'ZU'} <= set(non_eligible)

    # Check Eligible Schemes
    assert {'PA', 'PR', 'PS', 'MT', 'TA', 'AG', 'VI', 'FY'} <= set(eligible)

    for land_use in eligible:
        # Check Only one ecoscheme per land use
        assert len(eligible[land_use]) == 1

        # Check Pluriannuality Flag
        ecoschemes_with_pluri = [ecoscheme for ecoscheme in eligible[land_use]]

        if land_use in ('TA', 'VI', 'FY'):
            is_applicable = True  # Only P3/P4 and P6/P7 have pluriannuality in data
        else:
            is_applicable = False  # N/A and P5 don't qualify for pluriannuality

        assert ecoschemes_with_pluri[0]['pluriannuality_applicable'] is is_applicable

    # Check Rate Extraction (Tiered)
    p3p4_ecoschemes = eligible['TA'][0]
    assert p3p4_ecoschemes['rates']['Peninsular']['Tier_1'] == Decimal(
        '141.742439')
    assert p3p4_ecoschemes['rates']['Peninsular']['Threshold_ha'] == Decimal(
        '30.0')
