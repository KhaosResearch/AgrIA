import io
import pytest

from unittest.mock import MagicMock

from server.endpoints import chat

def test_hello_world(client):
    # --- ARRANGE --- #
    
    # Prepare mockups
    MOCK_RESPONSE = "Hello, World!"

    # Prepare inputs 
    # NONE. This is a GET method

    # --- ACT --- #

    response = client.get('/hello-world')
    
    # --- ASSERT --- #

    assert response.status_code == 200
    assert response.get_json()['response'] == MOCK_RESPONSE

@pytest.mark.parametrize(
        "test_name, user_input, expected_status, expected_response",
        [
            pytest.param(
                "Successful reply (200)",
                "Normal user input",
                200,
                "Normal mock reply.",
                id="Success_NormalInput"
            ),
            pytest.param(
                "Failure: No user input (400)",
                None,
                400,
                "No user input provided",
                id="Failure_NoInput"
            ),
        ]
)
def test_send_user_input_scenarios(
    client, monkeypatch, test_name, user_input, expected_status, expected_response
):
    # --- ARRANGE --- #
    
    # Prepare mockups
    monkeypatch.setattr(chat, "generate_user_response", lambda x: expected_response)

    # Prepare inputs
    data = {
        "userInput": user_input
    }
    
    # --- ACT --- #
    
    response = client.post('/send-user-input', data=data)
    
    # --- ASSERT --- #
    
    assert response.status_code == expected_status
    if expected_status != 200:
        assert response.get_json()['error'] == expected_response
    else:
        assert response.get_json()['response'] == expected_response

@pytest.mark.parametrize(
        "test_name, file_data, image_filename, is_detailed_desc, expected_status, expected_response",
        [
            pytest.param(
                "Successful sending (200)",
                io.BytesIO(b"This is dummy image data"),
                "test_image.jpg",
                "false",
                200,
                "A mock description of a sunny field.",
                id="Success_ImageSent"
            ),
            pytest.param(
                "Failure: No file (400)",
                None,
                None,
                "true",
                400,
                "No image file provided",
                id="Failure_NoFileData"
            ),
        ]
)
def test_send_image_scenarios(
    client, monkeypatch, test_name, file_data, image_filename, is_detailed_desc, expected_status, expected_response
):
    """Tests successful image upload and description retrieval."""
    
    # --- ARRANGE --- #
    # Prepare mockups        
    monkeypatch.setattr(chat, "get_image_description", lambda x, y: expected_response)
    
    # Prepare input
    data = {
        'image': (file_data, image_filename), 
        'isDetailedDescription': is_detailed_desc,  
    }
    
    # --- ACT --- #

    # 'multipart/form-data' is necessary for file uploads
    response = client.post(
        '/send-image', 
        data=data, 
        content_type='multipart/form-data'
    )
    
    # --- ASSERT --- #

    assert response.status_code == expected_status
    if expected_status != 200:
        assert response.get_json()["error"] == expected_response
    else:
        assert response.get_json()['response'] == expected_response

@pytest.mark.parametrize(
    "test_name, input_data, expected_status, expected_response",
    [
        # 1. Success Case (Happy Path) - Detailed Description
        pytest.param(
            "Success: Full Detailed Description",
            {
                'imageDate': '01/01/2024',
                'landUses': '["olive", "vine"]',
                'query': '{"type": "eco_regimen"}', # Optional field
                'imageFilename': 'test_parcel_image.png',
                'isDetailedDescription': 'true',
                'lang': 'en'
            },
            200,
            "This is a detailed description mock response.", # Mock return value
            id="Success_Detailed"
        ),
        # 2. Edge Case - Minimal Input (e.g., no query, basic description)
        pytest.param(
            "Success: Minimal Input, Basic Description",
            {
                'imageDate': '01/01/2024',
                'landUses': '["olive"]',
                'query': '{"type": "eco_regimen"}',
                'imageFilename': 'test_parcel_image_small.png',
                'isDetailedDescription': 'false', # isDetailedDescription is false
                'lang': 'es'
            },
            200,
            "Respuesta breve sobre la parcela.", # Mock return value,
            id="Success_Basic"
        ),
        # 3. Failure: Missing a crucial field (Assuming 'imageDate' is required)
        pytest.param(
            "Failure: Missing Image Date (400)",
            {
                # 'imageDate' is missing
                'landUses': '["olive", "vine"]',
                'query': '{"type": "eco_regimen"}',
                'imageFilename': 'test_parcel_image.png',
                'isDetailedDescription': 'true',
                'lang': 'en'
            },
            400,
            "No image date provided", # The expected 400 error message
            id="Failure_MissingDate"
        ),
        pytest.param(
            "Failure: Missing all data (400)",
            {},
            400,
            "No image date provided", # The expected 400 error message
            id="Failure_NoData"
        ),

    ]
)
def test_send_parcel_info_to_chat_scenarios(
    client, monkeypatch, test_name, input_data, expected_status, expected_response
):
    """Tests various scenarios for the /load-parcel-data-to-chat endpoint."""
    
    # --- ARRANGE --- #

    monkeypatch.setattr(chat, "get_parcel_description", lambda *args: expected_response)
    
    # --- ACT --- #

    response = client.post('/load-parcel-data-to-chat', data=input_data) 

    # --- ASSERT --- #
    
    assert response.status_code == expected_status
    response_json = response.get_json()

    if expected_status == 200:
        assert response_json['response'] == expected_response
    else:
        assert response_json['error'] == expected_response
        
@pytest.mark.parametrize(
    "test_name, history_data, input_data, expected_status, expected_response",
    [
        pytest.param(
            "Success: Got suggestion",
            "A list of past messages in the chat.",
            {
                "lang": "en" 
            },
            200,
            "A mock suggestion from the LLM.",
            id="Success_GotSuggestion"
        ),
        pytest.param(
            "Failure: No valid history provided",
            None,
            {
                "lang": "en" 
            },
            400,
            "No valid history provided.",
            id="Failure_NoHistory"
        ),
    ]
)
def test_get_input_suggestion_scenarios(
    client, monkeypatch, test_name, history_data, input_data, expected_status, expected_response
):
    # --- ARRANGE --- #
    
    # Prepare the mockups
    
    # 1. Create a Mock Chat Object
    # We use MagicMock to simulate the 'chat' instance
    mock_chat_instance = MagicMock()
    
    # Configure the mock instance to return the MOCK_HISTORY when get_history() is called
    mock_chat_instance.get_history.return_value = history_data 

    # 2. Patch the global 'chat' variable in the endpoint module with our mock instance
    # This prevents the AttributeError: 'NoneType' has no attribute 'get_history'
    monkeypatch.setattr(chat, "chat", mock_chat_instance)
    
    # 4. Prepare mock for the service function (as you did before)
    def mock_get_suggestion_for_chat(chat_history, lang):
        # We can also add an assertion here to check if the history was passed correctly
        assert chat_history == history_data
        return expected_response
        
    monkeypatch.setattr(chat, "get_suggestion_for_chat", mock_get_suggestion_for_chat)
        
    # --- ACT --- #
    
    response = client.post('/get-input-suggestion', data=input_data)
    
    # --- ASSERT --- #
    
    assert response.status_code == expected_status
    if expected_status != 200:
        assert response.get_json()['error'] == expected_response
    else:
        assert response.get_json()['response'] == expected_response

@pytest.mark.parametrize(
    "test_name, history_data, expected_status, expected_response",
    [
        pytest.param(
            "Success: History loaded",
            "A list of past messages in the chat.",
            200,
            "History loaded correctly!.",
            id="Success_HistoryLoaded"
        ),
        pytest.param(
            "Failure: No history available",
            None,
            400,
            "No valid history provided.",
            id="Failure_NoHistory"
        ),
    ]
)
def test_load_active_chat_history_scenarios(
    client, monkeypatch, test_name, history_data, expected_status, expected_response
):
    # --- ARRANGE --- #
    # Prepare mockups
    mock_chat_instance = MagicMock()
    mock_chat_instance.get_history.return_value = history_data 
    monkeypatch.setattr(chat, "chat", mock_chat_instance)
    def mock_get_role_and_content(user_input):
        return expected_response
    monkeypatch.setattr(chat, "get_role_and_content", mock_get_role_and_content)

    # Prepare inputs
    data = {}  # No need for input. THis is a GET method. history is fetched directly from chat
    
    # --- ACT --- #
    response = client.get('/load-active-chat-history')
    
    # --- ASSERT --- #
    assert response.status_code == expected_status
    if expected_status != 200:
        assert response.get_json()['error'] == expected_response
    else:
        assert response.get_json()['response'] == expected_response
