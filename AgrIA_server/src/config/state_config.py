from langchain_core.messages import AIMessage

from .constants import WELCOME_MESSAGE
from ..models.state_models import AgrIAState

AGRIA_STATE = AgrIAState(
    {
        "messages": [AIMessage(content=WELCOME_MESSAGE)],
        "lang": "es",
        "crop_metadata": None,
        "visual_description": None,
        "correction_feedback": None,
    }
)
