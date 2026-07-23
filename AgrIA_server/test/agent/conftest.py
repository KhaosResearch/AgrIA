import pytest
from unittest.mock import MagicMock
from langchain_core.messages import HumanMessage
from src.models.state_models import AgrIAState


@pytest.fixture
def mock_crop_json(tmp_path):
    """Provides sample crop metadata dictionary."""
    return {
        "parcel_id": "26002A001000010000EQ",
        "crop_type": "Secano",
        "surface_ha": 4.2,
    }


@pytest.fixture
def base_state():
    """Returns a baseline AgrIAState setup."""

    def _create_state(user_text: str) -> AgrIAState:
        return {
            "messages": [HumanMessage(content=user_text)],
            "lang": "es",
            "crop_metadata": None,
            "visual_description": None,
            "correction_feedback": None,
        }

    return _create_state


@pytest.fixture
def mock_llm_client(mocker):
    """Mocks the LocalChat / vLLM client to avoid network calls during fast tests."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"intent": "basic_chat", "confidence": 0.95}'
    mock_client.invoke.return_value = mock_response
    return mock_client
