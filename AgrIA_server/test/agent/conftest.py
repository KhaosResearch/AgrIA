import pytest
import uuid
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
def test_config():
    """Generates a unique thread_id per test run to keep tests isolated."""
    return {"configurable": {"thread_id": f"test_{uuid.uuid4()}"}}


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


@pytest.fixture(autouse=True)
def mock_local_chat(monkeypatch):
    """
    Dynamically mocks LocalChat.send_message based on the input context
    to pass validation loops and prevent GraphRecursionError in CI.
    """

    def dynamic_send_message(self_or_content, *args, **kwargs):
        # Handle call whether user_content is passed as 1st or 2nd arg
        if args:
            user_content = args[0]
        else:
            user_content = self_or_content

        content_str = str(user_content)
        mock_response = MagicMock()

        # 1. If called from report_generator or retry loop, return a compliant report
        if (
            "compile the agricultural report" in content_str
            or "###DESCRIBE_SHORT_IMAGE###" in content_str
        ):
            mock_response.text = """
### Informe de Análisis de Parcela

| Ecorregimen | Tipo | Superficie (ha) |
| :--- | :--- | :--- |
| **Rotación de Cultivos** | Secano | 4.2 |

**Resumen de Explotación:**
La parcela identificada con referencia 26002A001000010000EQ cuenta con un área total de Total_Parcel_Area_ha: 4.2 ha.
"""
            return mock_response

        # 2. If called from deterministic_router for intent classification
        if "Classify the intent" in content_str:
            if "###DESCRIBE_SHORT_IMAGE###" in content_str:
                mock_response.text = '{"intent": "report_generator", "confidence": 1.0}'
            elif (
                "ecorregímenes" in content_str.lower()
                and "importes" in content_str.lower()
            ):
                mock_response.text = (
                    '{"intent": "ecoschemes_rates", "confidence": 0.98}'
                )
            elif "ecorregímenes" in content_str.lower() or "pac" in content_str.lower():
                mock_response.text = '{"intent": "cap_query", "confidence": 0.95}'
            elif "sentido de la vida" in content_str.lower():
                mock_response.text = (
                    '{"intent": "fallback_rejection", "confidence": 0.98}'
                )
            else:
                mock_response.text = '{"intent": "basic_chat", "confidence": 0.95}'
            return mock_response

        # 3. Default basic chat response for standard chat nodes
        mock_response.text = (
            "Hola! Soy AgrIA. Respuesta simulada para pruebas de integración."
        )
        return mock_response

    # Patch send_message with our dynamic wrapper
    monkeypatch.setattr(
        "src.models.chat_models.LocalChat.send_message",
        dynamic_send_message,
    )
