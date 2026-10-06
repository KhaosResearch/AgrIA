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
        # CAP workflow starts empty on every conversation; the slot guard and
        # application nodes are the only writers of these fields.
        "cap_form_data": None,
        "assessment_report": None,
        "pending_action": None,
        "cap_workflow": None,
        "cap_alignment": None,
        "cap_rates": None,
    }
)
