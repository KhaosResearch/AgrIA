from server.services.ecoscheme_payments.main import calculate_ecoscheme_payment

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