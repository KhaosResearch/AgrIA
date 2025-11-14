import os
from flask import send_from_directory, make_response
from unittest.mock import MagicMock, mock_open
from server.endpoints import parcel_finder 

def test_load_parcel_description_success(client, monkeypatch):
    
    # --- ARRANGE ---
    # Prepare mockups
    # 1. Define the content that the mock file will "read"
    MOCK_RESPONSE = "This is a the parcel info file content."
    
    # 2. Mock the built-in 'open' function
    # mock_open() sets up a mock file object. read_data sets its content.
    mock_file_opener = mock_open(read_data=MOCK_RESPONSE)
    
    # Patch the built-in 'open' function, which is looked up by os.path.join
    monkeypatch.setattr("builtins.open", mock_file_opener)

    # 3. Mock os.path.exists to confirm the file is there
    # We patch it directly on the 'os' module object imported in the endpoint file
    monkeypatch.setattr(os.path, "exists", lambda x: True)
    
    # Prepare inputs 
    data = {
        "lang": "es" 
    }

    # --- ACT ---

    response = client.post('/load-parcel-description', data=data)
    
    # --- ASSERT ---

    # 1. Check status code
    assert response.status_code == 200
    
    # 2. Check content (which is the mock file content)
    assert response.get_json()['response'] == MOCK_RESPONSE
    
    # 3. Optional: Verify that 'open' was called with the correct filename
    # TEMP_DIR is imported in the endpoint, so we can't easily check its value here.
    # However, we can assert that the file was opened for reading.
    mock_file_opener.assert_called_once()

def test_find_parcel_success(client, monkeypatch):
    # --- ARRANGE --- #
    
    # Prepare mockups
    monkeypatch.setattr(parcel_finder, "reset_dir", lambda x: None)
    
    MOCK_CADASTRAL_VALUE = "MOCK_REF"
    def mock_check_cadastral_data(*args, **kwargs):
        return MOCK_CADASTRAL_VALUE
    monkeypatch.setattr(parcel_finder, "check_cadastral_data", mock_check_cadastral_data)

    MOCK_GEOMETRY = {"type": "Polygon"}
    MOCK_METADATA = "Mock Metadata String"
    MOCK_URL = "http://mock-url.com/image.png"
    def mock_get_parcel_image(*args, **kwargs):
        return MOCK_GEOMETRY, MOCK_METADATA, MOCK_URL
    monkeypatch.setattr(parcel_finder, "get_parcel_image", mock_get_parcel_image)

    # Prepare inputs 
    # Provide placeholder values for all expected form fields to prevent None/Type errors
    data = {
        'selectedDate': '2024-01-01', 
        'isFromCadastralReference': 'True', 
        'cadastralReference': 'A_CAD_REF',
        "parcelGeometry": "None", # Needs to be handled by the endpoint logic
        "parcelMetadata": "None",
        "coordinates": "1.0,2.0", # Will be split and mapped to float
        "province": "Mock",
        "municipality": "Mock",
        "polygon": "Mock",
        "parcelId": "Mock"
    }    # --- ACT --- #

    response = client.post('/find-parcel', data=data)
    
    # --- ASSERT --- #

    assert response.status_code == 200
    # The route constructs the final response dictionary
    MOCK_RESPONSE = {
        "cadastralReference": MOCK_CADASTRAL_VALUE, # Should be the value returned by check_cadastral_data
        "geometry": MOCK_GEOMETRY,
        "imagePath": MOCK_URL,
        "metadata": MOCK_METADATA,
    }
    assert response.get_json()['response'] == MOCK_RESPONSE

def test_is_coord_in_zone_false_success(client, monkeypatch):
    # --- ARRANGE --- #
    
    # Prepare mockups
    MOCK_RESPONSE = True
    def mock_is_coord_in_zones(lat,lon):
        return MOCK_RESPONSE
    monkeypatch.setattr(parcel_finder, "is_coord_in_zones", mock_is_coord_in_zones)
    
    # Prepare inputs 
    data = {
        "lat": "1.0", 
        "lng": "2.0" 
    }

    # --- ACT --- #

    response = client.post('/is-coord-in-zone', data=data)
    
    # --- ASSERT --- #

    assert response.status_code == 200
    assert response.get_json()['response'] == MOCK_RESPONSE

def test_uploaded_file_success(client, monkeypatch):
    # --- ARRANGE --- #
    
    # Prepare mockups
    # When send_from_directory is called, we want it to return a basic mock response
    MOCK_FILE_CONTENT = "Mock file content stream"
    
    # 2. Mock the send_from_directory function
    def mock_send_from_directory(*args, **kwargs):
        return MOCK_FILE_CONTENT
    monkeypatch.setattr(parcel_finder, "send_from_directory", mock_send_from_directory)
    
    # 3. Define the expected filename
    MOCK_FILENAME = "test_image.jpg"
    
    # --- ACT --- #

    response = client.get(f'/uploads/{MOCK_FILENAME}')
    
    # --- ASSERT --- #

    assert response.status_code == 200
    assert response.data.decode('utf-8') == MOCK_FILE_CONTENT
    assert response.headers["Cache-Control"] == "no-cache, no-store, must-revalidate"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Expires"] == "0"
