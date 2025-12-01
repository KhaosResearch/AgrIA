import os
import pytest

from flask import make_response
from unittest.mock import MagicMock, mock_open

from server.endpoints import parcel_finder

# Define mock return values once
MOCK_CADASTRAL_VALUE = "MOCK_REF_20CHAR_00000"
MOCK_GEOMETRY = {"type": "Polygon"}
MOCK_METADATA = "Mock Metadata String"
MOCK_URL = "http://mock-url.com/image.png"

MOCK_FILE_CONTENT = "Mock file content stream"

# Generate parcel finder fixture


@pytest.fixture
def find_parcel_mocks(monkeypatch):
    """Mocks common dependencies for all /find-parcel tests."""

    # Mock external utility calls
    mock_reset_dir = MagicMock(return_value=None)
    monkeypatch.setattr(parcel_finder, "reset_dir", mock_reset_dir)

    # Mock check_cadastral_data to return a valid reference by default
    mock_check_cadastral_data = MagicMock(return_value=MOCK_CADASTRAL_VALUE)
    monkeypatch.setattr(parcel_finder, "check_cadastral_data",
                        mock_check_cadastral_data)

    # Mock get_parcel_image to return the three expected values
    mock_get_parcel_image = MagicMock(
        return_value=(MOCK_GEOMETRY, MOCK_METADATA, MOCK_URL))
    monkeypatch.setattr(parcel_finder, "get_parcel_image",
                        mock_get_parcel_image)

    # Yield the expected success response structure for assertions
    return {
        "cadastralReference": MOCK_CADASTRAL_VALUE,
        "geometry": MOCK_GEOMETRY,
        "imagePath": MOCK_URL,
        "metadata": MOCK_METADATA,
    }


def mock_send_from_directory_success(*args, **kwargs):
    return MOCK_FILE_CONTENT

# Mocks the function raising a FileNotFoundError (usually done by Flask internally for missing files)


def mock_send_from_directory_missing(*args, **kwargs):
    # This simulates Flask raising a 404/403/other error internally, which our endpoint doesn't catch
    # If the file is missing, send_from_directory typically raises a werkzeug.exceptions.NotFound
    # But since we're mocking, we'll raise a common I/O error or simulate a 404 response
    return make_response("File Not Found", 404)

# --- LOAD PARCEL ---


@pytest.mark.parametrize(
    "test_name, desc_response, expected_status, expected_error",
    [
        pytest.param(
            "File exists and found (200 - Happy path)",
            "This is a the parcel info file content",
            200,
            True,
            id="Success_FileFound"
        ),  # Success case (assuming True is the mock response)
        pytest.param(
            "File not found (200 - Expected behaviour)",
            "...",
            200,
            False,
            id="Success_FileNotFound"
        ),  # File not found case (expected)
    ],
)
def test_load_parcel_description_scenarios(
    client, monkeypatch, test_name, desc_response, expected_status, expected_error
):
    # --- ARRANGE ---
    # Prepare mockups
    mock_file_opener = mock_open(read_data=desc_response)
    monkeypatch.setattr("builtins.open", mock_file_opener)
    monkeypatch.setattr(os.path, "exists", lambda x: expected_error)

    # Prepare inputs
    data = {
        "lang": "es"
    }

    # --- ACT ---
    response = client.post('/load-parcel-description', data=data)

    # --- ASSERT ---
    assert response.status_code == expected_status

    if expected_status == 200:
        assert response.get_json()['response'] == desc_response
    else:
        assert response.get_json()['error'] == desc_response

# --- FIND PARCEL ---

# Set all tests parameters


@pytest.mark.parametrize(
    "test_name, input_data, expected_status, expected_content_key, expected_content_value, patch_cadastral_check",
    [
        pytest.param(
            "Success Case (Happy Path)",
            {
                'selectedDate': '2024-01-01',
                'isFromCadastralReference': 'True',
                'cadastralReference': 'A_CAD_REF',
                "parcelGeometry": "None", "parcelMetadata": "None",
                "coordinates": "1.0,2.0", "province": "Mock",
                "municipality": "Mock", "polygon": "Mock", "parcelId": "Mock"
            },
            200,
            'response',
            None,  # Will be set to the fixture's success dictionary
            None,  # No special patch needed
            id="Success_ParcelFound"
        ),
        pytest.param(
            "Failure: Missing Selected Date (400)",
            {
                'isFromCadastralReference': 'True',
                'cadastralReference': 'A_CAD_REF',
                # 'selectedDate' is missing
            },
            400,
            'error',
            "No date provided",
            None,
            id="Failure_MissingDate"

        ),
        pytest.param(
            "Failure: Bad Coordinates Format (500)",
            {
                'selectedDate': '2024-01-01',
                'isFromCadastralReference': 'True',
                'coordinates': 'abc',  # Invalid input
            },
            500,
            'error',
            "could not convert string to float:",  # Partial match
            None,
            id="Failure_BadCoords"

        ),
        pytest.param(
            "Failure: Bad Cadastral Reference (500)",
            {
                'selectedDate': '2024-01-01',
                'isFromCadastralReference': 'True',
                'cadastralReference': 'BAD_REF',
                'coordinates': '1.0,2.0'
            },
            500,
            'error',
            "The cadastral reference must have a length of 20 characters",
            # Patch check_cadastral_data to explicitly raise the expected error
            lambda *args: (_ for _ in ()).throw(ValueError(
                "The cadastral reference must have a length of 20 characters")),
            id="Failure_BadCadastralRef"

        ),
        pytest.param(
            "Failure: Missing ALL data (500 - Iterable)",
            {},  # Empty data
            500,
            'error',
            "argument of type 'NoneType' is not iterable",
            None,
            id="Failure_MissingAllData"
        ),
    ],
)
def test_find_parcel_scenarios(
    client, monkeypatch, find_parcel_mocks, test_name,
    input_data, expected_status, expected_content_key,
    expected_content_value, patch_cadastral_check
):
    """Runs all success and failure scenarios for the /find-parcel endpoint."""

    # ARRANGE: Apply special patches if required by the scenario
    if patch_cadastral_check:
        monkeypatch.setattr(
            parcel_finder, "check_cadastral_data", patch_cadastral_check)

    # Set expected success value if the test is a success case
    if expected_status == 200:
        expected_content_value = find_parcel_mocks

    # ACT
    response = client.post('/find-parcel', data=input_data)

    # ASSERT
    assert response.status_code == expected_status

    # Extract the response content
    response_json = response.get_json()
    actual_content = response_json.get(expected_content_key)

    # Assert on exact match or partial match for error messages
    if "could not convert string to float" in str(expected_content_value):
        assert expected_content_value in actual_content
    else:
        assert actual_content == expected_content_value

# --- IS COORD ZONE ---


@pytest.mark.parametrize(
    "lat_input, lng_input, expected_status, expected_response",
    [
        pytest.param(
            "40.400409",
            "-3.631434",
            200,
            True,
            id="Success_CoordInZone"
        ),
        pytest.param(
            "-40.400409",
            "3.631434",
            200,
            False,
            id="Success_CoordNotInZone"
        ),

        pytest.param(
            "abc",
            "1.0",
            400,
            "Invalid or missing coordinates",
            id="Failure_BadLat"
        ),
        pytest.param(
            "1.0",
            "xyz",
            400,
            "Invalid or missing coordinates",
            id="Failure_BadLng"
        ),
        pytest.param(
            None,
            None,
            400,
            "Invalid or missing coordinates",
            id="Failure_NoCoords"
        ),
    ],
)
def test_is_coord_in_zone_scenarios(
    client, monkeypatch, lat_input, lng_input, expected_status, expected_response
):
    # --- ARRANGE ---
    def mock_is_coord_in_zones(lat, lon):
        return expected_response
    monkeypatch.setattr(parcel_finder, "is_coord_in_zones",
                        mock_is_coord_in_zones)

    data = {"lat": lat_input, "lng": lng_input}

    # --- ACT ---
    response = client.post('/is-coord-in-zone', data=data)

    # --- ASSERT ---
    assert response.status_code == expected_status

    if expected_status == 200:
        # Assert the success response structure
        assert response.get_json()['response'] == expected_response
    else:
        # Assert the error message structure
        assert response.get_json()['error'] == expected_response

# --- UPLOAD IMAGE FILE ---


@pytest.mark.parametrize(
    "test_name, filename, mock_func, expected_status, expected_content_match",
    [
        pytest.param(
            "Success Case: Image File",
            "test_image.jpg",
            mock_send_from_directory_success,
            200,
            MOCK_FILE_CONTENT,
            id="Success_FileUploaded"
        ),
        pytest.param(
            "Edge Case: File Not Found (404)",
            "missing_file.png",
            mock_send_from_directory_missing,
            404,
            "File Not Found",
            id="Failure_NotFound"
        ),
    ]
)
def test_uploaded_file_scenarios(
    client, monkeypatch, test_name, filename, mock_func,
    expected_status, expected_content_match
):
    """Tests various scenarios for serving files from the /uploads endpoint."""

    # --- ARRANGE ---
    # Patch the send_from_directory function with the specific mock for this scenario
    monkeypatch.setattr(parcel_finder, "send_from_directory", mock_func)

    # --- ACT ---
    response = client.get(f'/uploads/{filename}')

    # --- ASSERT ---
    assert response.status_code == expected_status

    # Check custom headers ONLY if the response was successfully handled by the route (status 200)
    if expected_status == 200:
        assert response.headers["Cache-Control"] == "no-cache, no-store, must-revalidate"
        assert response.headers["Pragma"] == "no-cache"
        assert response.headers["Expires"] == "0"

        # Check the content
        assert response.data.decode('utf-8') == expected_content_match

    # Check the content for 404/500 errors (if you expect a specific error message body)
    elif expected_status in (404, 500):
        # Note: Flask's default error pages may have different structures (JSON vs HTML).
        # We check if the expected error string is contained in the response body.
        assert expected_content_match in response.data.decode('utf-8')
