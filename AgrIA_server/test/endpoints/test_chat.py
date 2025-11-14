import io
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

def test_send_user_input_success(client, monkeypatch):
    # --- ARRANGE --- #
    
    # Prepare mockups
    MOCK_RESPONSE = "A mock reply from the LLM."
    def mock_generate_user_response(user_input):
        return MOCK_RESPONSE
    monkeypatch.setattr(chat, "generate_user_response", mock_generate_user_response)

    # Prepare inputs
    data = {
        "userInput": "This is the user input."
    }
    
    # --- ACT --- #
    
    response = client.post('/send-user-input', data=data)
    
    # --- ASSERT --- #
    
    assert response.status_code == 200
    assert response.get_json()['response'] == MOCK_RESPONSE

def test_send_image_success(client, monkeypatch):
    """Tests successful image upload and description retrieval."""
    
    # --- ARRANGE --- #
    
    # Prepare mockups
    # 1. Define the mocked return value for the service function
    MOCK_RESPONSE = "A mock description of a sunny field."
    
    # 2. Create a mock function to replace the actual service function
    def mock_get_image_description(file, is_detailed):
        # We don't care about the file/boolean here, just that it was called.
        return MOCK_RESPONSE
        
    # 3. Use monkeypatch to replace the real service function with our mock
    # This prevents the test from executing the complex image processing logic.
    monkeypatch.setattr(chat, "get_image_description", mock_get_image_description)
    
    # 4. Create a dummy file object for the request
    # Flask/Werkzeug expects a file-like object
    dummy_file = io.BytesIO(b"This is dummy image data")
    
    # Prepare input
    # 5. Prepare the data payload for the POST request
    data = {
        'image': (dummy_file, 'test_image.jpg'), 
        'isDetailedDescription': 'true' 
    }
    
    # --- ACT --- #

    # 6. Execute the POST request
    # 'multipart/form-data' is necessary for file uploads
    response = client.post(
        '/send-image', 
        data=data, 
        content_type='multipart/form-data'
    )
    
    # --- ASSERT --- #

    # 7. Assertions
    assert response.status_code == 200
    assert response.get_json()['response'] == MOCK_RESPONSE

def test_send_image_missing_file(client):
    """Tests the endpoint returns 400 when no image file is provided."""
    # --- ARRANGE --- #
    
    data = {}
    
    # --- ACT --- #
    
    response = client.post('/send-image', data=data)
    
    # --- ASSERT --- #
    
    assert response.status_code == 400
    assert 'error' in response.get_json()
    assert response.get_json()['error'] == 'No image file provided'

def test_send_parcel_info_to_chat_success(client, monkeypatch):
    """Tests the /load-parcel-data-to-chat endpoint with valid data."""

    # --- ARRANGE --- #

    # Prepare mockups
    MOCK_RESPONSE = "Parcel description generated successfully."
    
    def mock_get_parcel_description(*args):
        # We ensure it was called and immediately return the mock text
        return MOCK_RESPONSE
        
    # Patch the function where the endpoint looks it up
    # We patch the function on the 'chat' endpoint module
    monkeypatch.setattr(chat, "get_parcel_description", mock_get_parcel_description)

    # Prepare input
    # NOTE: Flask test client requires these to be strings/form data, 
    # even if your route immediately converts them via json.loads()
    data = {
        'imageDate': '01/01/2024',
        'landUses': '["olive", "vine"]', # Must be a string
        'query': '{"type": "eco_regimen"}', # Must be a string
        'imageFilename': 'test_parcel_image.png',
        'isDetailedDescription': 'true',
        'lang': 'en'
    }

    # --- ACT --- #

    # No file upload, so standard form data is fine
    response = client.post('/load-parcel-data-to-chat', data=data) 

    # --- ASSERT --- #
    
    # Verify the outcome
    assert response.status_code == 200
    assert response.get_json()['response'] == MOCK_RESPONSE

def test_get_input_suggestion_success(client, monkeypatch):
    # --- ARRANGE --- #
    
    # Prepare the mockups
    # 1. Prepare the mocked chat history result
    MOCK_HISTORY = "A list of past messages in the chat."
    
    # 2. Create a Mock Chat Object
    # We use MagicMock to simulate the 'chat' instance
    mock_chat_instance = MagicMock()
    
    # Configure the mock instance to return the MOCK_HISTORY when get_history() is called
    mock_chat_instance.get_history.return_value = MOCK_HISTORY 

    # 3. Patch the global 'chat' variable in the endpoint module with our mock instance
    # This prevents the AttributeError: 'NoneType' has no attribute 'get_history'
    monkeypatch.setattr(chat, "chat", mock_chat_instance)
    
    # 4. Prepare mock for the service function (as you did before)
    MOCK_SUGGESTION = "A mock suggestion from the LLM."
    def mock_get_suggestion_for_chat(chat_history, lang):
        # We can also add an assertion here to check if the history was passed correctly
        assert chat_history == MOCK_HISTORY
        return MOCK_SUGGESTION
        
    monkeypatch.setattr(chat, "get_suggestion_for_chat", mock_get_suggestion_for_chat)
    
    # Prepare inputs
    data = {
        "lang": "es" 
    }
    
    # --- ACT --- #
    
    response = client.post('/get-input-suggestion', data=data)
    
    # --- ASSERT --- #
    
    assert response.status_code == 200
    assert response.get_json()['response'] == MOCK_SUGGESTION
    
    # Optional: Verify the mock was called
    mock_chat_instance.get_history.assert_called_once()

def test_load_active_chat_history_success(client, monkeypatch):
    # --- ARRANGE --- #
    
    # Prepare mockups
    MOCK_HISTORY = "A list of past messages in the chat."
    mock_chat_instance = MagicMock()
    mock_chat_instance.get_history.return_value = MOCK_HISTORY 
    monkeypatch.setattr(chat, "chat", mock_chat_instance)
    MOCK_RESPONSE = "History loaded correctly!."
    def mock_get_role_and_content(user_input):
        return MOCK_RESPONSE
    monkeypatch.setattr(chat, "get_role_and_content", mock_get_role_and_content)

    # Prepare inputs
    data = {}  # No need for input. THis is a GET method. history is fetched directly from chat
    
    # --- ACT --- #
    
    response = client.get('/load-active-chat-history')
    
    # --- ASSERT --- #
    
    assert response.status_code == 200
    assert response.get_json()['response'] == MOCK_RESPONSE
