from typing import TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing import Annotated


# Define the clean State representation for LangGraph
class AgrIAState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    lang: str  # "es" or "en"
    crop_metadata: Optional[dict]  # The JSON calculated from your tools
    cap_form_data: Optional[dict]  # CAP slots collected across turns, by field name
    assessment_report: Optional[str]  # Raw parcel assessment markdown (was TEMP_DIR)
    pending_action: Optional[str]  # e.g. "AWAITING_CAP_DOC", "AWAITING_SLOT:surface_ha"
    cap_workflow: Optional[str]  # "collect" | "assess" | "ready" | "unrelated"
    cap_alignment: Optional[dict]  # Slot guard verdict for the latest user turn
    cap_rates: Optional[dict]  # Explicit EUR/ha rate table used to reproduce amounts
    visual_description: Optional[str]
    correction_feedback: Optional[str]


class CapSlotGuardOutput(BaseModel):
    """Structured output of the single-call CAP slot guard."""

    classification: str = Field(
        description=(
            "One of: answer, correction, missing_information, topic_change. "
            "'answer' answers the pending question, 'correction' fixes an "
            "earlier value, 'missing_information' volunteers a new value, "
            "'topic_change' is unrelated to the CAP application."
        )
    )
    confidence: float = Field(ge=0.0, le=1.0)
    slots: dict = Field(
        default_factory=dict,
        description="Field name -> value found in the message. Empty if none.",
    )
    reason: str = Field(default="", description="Short justification")
