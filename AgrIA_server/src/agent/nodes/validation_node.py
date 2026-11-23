from typing import Literal

import structlog
from langchain_core.messages import HumanMessage

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
    logger.debug(f"GENERATED REPORT:\n{generated_report}")

    if metadata:
        total_area = str(metadata.get("Total_Parcel_Area_ha", ""))
        eng_fmt = total_area
        spa_fmt = total_area.replace(".", ",")
        if not (eng_fmt in generated_report or spa_fmt in generated_report):
            errors.append(
                f"Missing critical metadata value: Total parcel area ({total_area} ha) must be explicitly stated."
            )
    elif "using last user message" not in generated_report.lower():
        logger.warning(
            "⚠️  No parcel land use metadata detected. Moving on with unvalid report..."
        )
        i = len(messages) - 1
        usr_msg = None
        while i >= 0 and not usr_msg:
            usr_msg = (
                messages[i].content if isinstance(messages[i], HumanMessage) else None
            )
            i -= 1
        errors.append(
            f"Insert '_Using last user message as land use metadata..._<br>'at the beginning of the report and use this as metadata:\n<usr_msg>\n{usr_msg}\n</usr_msg>\n\nDo not include this in the report, only the requested insertion."
        )

    # TODO: Use col names in tables as validation markers!!

    # Evaluate validation outcome
    if len(errors) > 0:
        feedback_note = "CRITICAL CORRECTION REQUIRED:\n" + "\n".join(
            f"- {err}" for err in errors
        )
        logger.warning(feedback_note)
        return {"correction_feedback": feedback_note}

    # Clear the metadata in the returned update: the previous in-place assignment
    # was discarded by LangGraph, so the value survived into the next turn.
    # Safe because a PASSED verdict exits the graph immediately.
    return {"correction_feedback": "PASSED"}


MAX_REPORT_RETRIES = 2


def evaluation_router_edge(state: AgrIAState) -> Literal["report_generator", "__end__"]:
    """Determines whether to exit or loop back based on validation feedback.

    Bounded: after MAX_REPORT_RETRIES failed attempts the loop exits with the
    last (imperfect) report rather than recursing indefinitely.
    """
    feedback = state.get("correction_feedback", "")

    if feedback == "PASSED":
        logger.info("-> [VALIDATION PASSED]: Report meets all compliance rules.")
        return "__end__"  # LangGraph's native exit keyword

    retry_count = (state.get("report_retry_count") or 0) + 1
    if retry_count > MAX_REPORT_RETRIES:
        logger.warning(
            f"-> [VALIDATION GAVE UP]: Max retries ({MAX_REPORT_RETRIES}) exceeded. "
            f"Returning last attempt."
        )
        return "__end__"

    logger.warning(
        f"-> [VALIDATION FAILED]: Loop correction triggered (attempt {retry_count}/{MAX_REPORT_RETRIES}).\n"
        f"Feedback: {feedback}"
    )
    return "report_generator"
