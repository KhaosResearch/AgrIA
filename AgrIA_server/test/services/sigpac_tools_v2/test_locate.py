import pytest

from conftest import MOCK_CADASTRAL_REF, MOCK_RESPONSE_JSON
from server.services.sigpac_tools_v2 import locate as sigpac_locate


@pytest.mark.parametrize(
    "test_name, lat, lon, crs, api_json_return, expected_exception, expected_error_match",
    [
        pytest.param(
            "Success_ValidCoords",
            40.0, -3.0, "4258",
            MOCK_RESPONSE_JSON,  # Full, valid list of JSON objects
            None,
            None,
            id="Success_RefGenerated"
        ),
        pytest.param(
            "Failure_EmptyResponse",
            40.0, -3.0, "4258",
            [], # Empty list from API
            ValueError,
            "Invalid JSON returned by SIGPAC",
            id="Failure_EmptyList_ValueError"
        ),
        pytest.param(
            "Failure_InvalidJSONFormat",
            40.0, -3.0, "4258",
            [{"error_data": 123}], # Missing expected keys like 'provincia'
            ValueError,
            "Invalid JSON returned by SIGPAC",
            id="Failure_KeyError_ValueError"
        ),
        pytest.param(
            "Failure_MalformedAPIBody",
            40.0, -3.0, "4258",
            {"status": "error"}, # A dict, which cannot be indexed by [0]
            ValueError,
            "Invalid JSON returned by SIGPAC",
            id="Failure_TypeError_ValueError"
        ),
    ]
)
def test_generate_cadastral_ref_from_coords_scenarios(
    mock_sigpact_tools_v2_dependencies,
    test_name, lat, lon, crs, api_json_return, expected_exception, expected_error_match
):
    # Retrieve mocks
    mock_requests_get = mock_sigpact_tools_v2_dependencies["mock_requests_get"]
    mock_json_body = mock_sigpact_tools_v2_dependencies["mock_response_json"]
    mock_build_ref = mock_sigpact_tools_v2_dependencies["mock_build_cadastral_reference"]
    
    #  Reset mocks
    mock_requests_get.reset_mock()
    mock_json_body.reset_mock()
    mock_build_ref.reset_mock()

    # --- ARRANGE (Conditional Mocks) ---
    
    # Set the return value of the response's .json() method for the current test case
    mock_json_body.return_value = api_json_return
    
    # Ensure the build mock returns the expected success value
    mock_build_ref.return_value = MOCK_CADASTRAL_REF


    # --- ACT & ASSERT ---
    if expected_exception:
        # Expected Failure
        with pytest.raises(expected_exception, match=expected_error_match):
            sigpac_locate.get_cadastral_data_from_coords(lat, lon, crs)
            
        # Verify mocks were called up to the point of failure
        mock_requests_get.assert_called_once()
        mock_json_body.assert_called_once()
        # build_cadastral_reference should NOT be called on failure
        mock_build_ref.assert_not_called()
            
    else:
        # Expected Success
        cadastral_ref = sigpac_locate.get_cadastral_data_from_coords(lat, lon, crs)
        
        # 1. Check return value
        assert cadastral_ref == MOCK_CADASTRAL_REF
        
        # 2. Verify all mocks were called
        mock_requests_get.assert_called_once()
        mock_json_body.assert_called_once()
        mock_build_ref.assert_called_once() 
        
        # 3. Optional: Verify build_cadastral_reference was called with the correctly processed arguments (14, 48, 001, 00199)
        # Note: Based on MOCK_RESPONSE_JSON: "provincia": 14, "municipio": 48, "poligono": 1, "parcela": 199
        mock_build_ref.assert_called_once_with(
            '14-', # provincia (zfill(2) + '-')
            '048-', # municipio (zfill(3) + '-')
            '001', # poligono (zfill(3))
            '00199' # parcel (zfill(5))
        )