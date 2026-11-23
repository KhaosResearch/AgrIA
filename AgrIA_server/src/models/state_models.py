from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


# Define the clean State representation for LangGraph
class AgrIAState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    lang: str  # "es" or "en"
    crop_metadata: dict | None  # The JSON calculated from your tools
    cap_form_data: dict | None  # CAP slots collected across turns, by field name
    assessment_report: str | None  # Raw parcel assessment markdown (was TEMP_DIR)
    pending_action: str | None  # e.g. "AWAITING_CAP_DOC", "AWAITING_SLOT:surface_ha"
    cap_workflow: str | None  # "collect" | "assess" | "ready" | "unrelated"
    cap_alignment: dict | None  # Slot guard verdict for the latest user turn
    cap_rates: dict | None  # Explicit EUR/ha rate table used to reproduce amounts
    visual_description: str | None
    correction_feedback: str | None
    report_retry_count: int | None  # Bounded retry counter for the report validation loop
    secondary_intent: str | None  # A second intent the router detected; the primary
    # node is asked to also address it in its reply (multi-intent, no topology change)


# Single source of truth for the intents the router may emit. The graph's edge map,
# the classifier's validity check and the few-shot prompt all derive from this set,
# so adding or renaming an intent is one edit instead of three.
INTENT_REGISTRY: frozenset[str] = frozenset(
    {
        "report_generator",
        "basic_chat",
        "app_usage",
        "cap_query",
        "ecoschemes_rates",
        "fallback_rejection",
        "cap_document_inspector",
        "cap_slot_guard",
        "cap_application",
        "cap_form_status",
        "clear_cap_workflow",
    }
)


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
