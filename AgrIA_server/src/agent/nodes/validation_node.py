import structlog

from langchain_core.messages import HumanMessage
from typing import Literal

from ...models.state_models import AgrIAState

logger = structlog.get_logger(__file__)


def validate_report_node(state: AgrIAState) -> dict:
    """
    Evaluates the generated markdown report against hard compliance constraints.
    Does not use an LLM call—uses fast, programmatic validation.
    """
    messages = state["messages"]
    generated_report = str(messages[-1].content) if messages else ""
    metadata = state.get("crop_metadata", {})
    errors = []

    # Rule 1: Structural Markdown Check (Must contain at least one Markdown Table)
    if "|" not in generated_report:
        errors.append(
            "Missing required structured Markdown tables for Eco-Schemes or Calculations."
        )

    # Rule 2: Critical Data Check (Must reference the total parcel area value)
    print("GENERATED REP\n", generated_report)

    if metadata:
        total_area = str(metadata.get("Total_Parcel_Area_ha", ""))
        eng_fmt = total_area
        spa_fmt = total_area.replace(".", ",")
        if not (eng_fmt in generated_report or spa_fmt in generated_report):
            errors.append(
                f"Missing critical metadata value: Total parcel area ({total_area} ha) must be explicitly stated."
            )
    elif not "using last user message" in generated_report.lower():
        logger.warning(
            "⚠️  No parcel land use metadata detected. Moving on with unvalid report..."
        )
        i = len(messages) -1
        usr_msg = None
        while i >= 0 and not usr_msg:
            usr_msg = messages[i].content if isinstance(messages[i], HumanMessage) else None
            i -= 1
        errors.append(
            f"Insert '_Using last user message as land use metadata...<br>_'at the beginning of the report and use this as metadata:\n<usr_msg>\n{usr_msg}\n</usr_msg>\n\nDo not include this in the report, only the requested insertion."
        )

    # TODO: Use col names in tables as validation markers!!

    # Evaluate validation outcome
    if len(errors) > 0:
        feedback_note = "CRITICAL CORRECTION REQUIRED:\n" + "\n".join(
            f"- {err}" for err in errors
        )
        logger.warning(feedback_note)
        return {"correction_feedback": feedback_note}

    state["crop_metadata"] = (
        None  # Reset crop metadata after successful validation
    )
    return {"correction_feedback": "PASSED"}


def evaluation_router_edge(state: AgrIAState) -> Literal["report_generator", "__end__"]:
    """Determines whether to exit or loop back based on validation feedback."""
    feedback = state.get("correction_feedback", "")

    if feedback == "PASSED":
        logger.info("-> [VALIDATION PASSED]: Report meets all compliance rules.")
        return "__end__"  # LangGraph's native exit keyword

    logger.warning(
        f"-> [VALIDATION FAILED]: Loop correction triggered.\nFeedback: {feedback}"
    )
    return "report_generator"
