import json
import structlog

from langchain_core.messages import AIMessage
from pathlib import Path
from typing import Any, Dict, List, Tuple

from ...benchmark.vlm.constants import OG_CLASSIFICATION_FILEPATH
from ...config.constants import CAP_FORMS_PATH
from ...models.chat_models import LocalChat
from ...models.state_models import AgrIAState
from .cap_slot_guard_node import guard_ack, topic_change_message
from ...utils.cap_form_utils import (
    load_cap_rates,
    build_form_mapping,
    estimated_amounts,
    first_missing_slot,
    merge_slots,
    validate_application,
)
from ...utils.chat_utils import get_recent_history
from ...utils.nodes_utils import load_prompt_asset

logger = structlog.get_logger(__name__)

APPLICATION_CONTEXT_TOKENS = 20000


def _load_ecoscheme_classification() -> str:
    """Eco-scheme reference table; failure degrades to an empty block."""
    try:
        return OG_CLASSIFICATION_FILEPATH.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("cap_ecoscheme_classification_unavailable", error=str(exc))
        return ""


def _last_user_text(messages: list) -> str:
    """Flatten the final message content, tolerating multimodal part lists."""
    if not messages:
        return ""
    content = messages[-1].content
    if isinstance(content, list):
        return " ".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and "text" in part
        )
    return str(content)


def _apply_alignment(
    state: AgrIAState,
) -> Tuple[dict, List[str]]:
    """Merge the guard's schema-gated slots into `cap_form_data`.

    This node is the only writer of `cap_form_data`, so every write path (PDF
    extraction and free text) converges here. Returns (merged_slots, new_names).
    """
    alignment = state.get("cap_alignment") or {}
    incoming = alignment.get("slots") or {}
    merged = merge_slots(state.get("cap_form_data"), incoming)
    new_names = [
        name
        for name in incoming
        if merged.get(name) != (state.get("cap_form_data") or {}).get(name)
    ]
    return merged, new_names


def cap_application_node(state: AgrIAState, client, model_name: str) -> Dict[str, Any]:
    """LangGraph Node: advance the CAP application workflow.

    Order of operations is deliberate and deterministic:
      1. merge any slots extracted by the guard / PDF inspector into state;
      2. run `validate_application` — an invalid application is never reported;
      3. when required fields remain, ask exactly one bilingual question and set
         `pending_action` so the graph can resume;
      4. only once valid, ask the LLM to phrase the mapped form and the
         reproducible estimated amounts.
    """
    lang = state.get("lang", "es")
    messages = state.get("messages", [])
    crop_metadata = state.get("crop_metadata")
    assessment_report = state.get("assessment_report")

    alignment = state.get("cap_alignment") or {}
    classification = alignment.get("classification")

    # The guard judged the message unrelated to the application. Do not touch any
    # field and do not clear `pending_action`: the workflow stays resumable and
    # the farmer can answer the outstanding question again.
    if classification == "topic_change" and not alignment.get("slots"):
        return {
            "cap_alignment": None,
            "messages": [AIMessage(content=topic_change_message(lang))],
        }

    slots, new_names = _apply_alignment(state)
    pending_action = state.get("pending_action")

    # A correction must not be immediately overwritten by the next question.
    if new_names:
        pending_action = None

    report = validate_application(slots)
    next_slot = first_missing_slot(slots, lang)

    # The alignment is consumed here; leaving it in state would re-merge it on
    # every later turn and mask a later correction.
    update: Dict[str, Any] = {"cap_form_data": slots, "cap_alignment": None}

    if not report["valid"]:
        # Ask one question at a time; keep the workflow in collection mode.
        ask = next_slot
        if not ask:
            # Required fields are present but something is unusable (bad enum,
            # out-of-range surface). Surface the error rather than guessing.
            logger.warning("cap_application_invalid", errors=report["errors"])
        logger.info(
            "cap_application_awaiting_slot",
            slot=ask["name"] if ask else None,
            errors=report["errors"],
        )
        pending_action = f"AWAITING_SLOT:{ask['name']}" if ask else pending_action
        # Confirm what was accepted before asking the next question, so a
        # correction is visibly applied.
        ack = guard_ack(slots, new_names, lang)
        update.update(
            {
                "pending_action": pending_action,
                "cap_workflow": "collect",
                "messages": [
                    AIMessage(
                        # Field names are internal schema identifiers, not farmer-facing
                        # language, so the reasons go to the log rather than the reply.
                        content=f"{ack}\n{ask['question']}"
                        if ask
                        else f"{ack}\nSome details need correcting, please tell me again."
                    )
                ],
            }
        )
        return update

    # Valid application: build the deterministic mapping and amounts.
    mapping = build_form_mapping(slots)
    # Amounts come from an explicit rate table in state: without it no figure is
    # produced at all, rather than a plausible-looking guess.
    # State rates (endpoint/admin supplied) win; otherwise the versioned asset.
    amounts = estimated_amounts(slots, state.get("cap_rates") or load_cap_rates())
    update.update({"cap_workflow": "ready", "pending_action": None})

    raw_instruction = load_prompt_asset("CAP_APPLICATION.md").replace(
        "{lang}", "Spanish" if lang == "es" else "English"
    )
    cap_form_example = Path(
        CAP_FORMS_PATH / "cap_form_redacted_JM_completed.md"
    ).read_text(encoding="utf-8")
    cap_form_instructions = f"Use the following example of cap form for plant cover ecoscheme application to guide the user. Use the corresponding headers and options on the form to help the user apply for all calculated ecoschemes on their parcel:\n\n<cap_form_example>\n{cap_form_example}\n<cap_form_example>"

    system_instruction = f"{raw_instruction}\n\n<classification>\n{_load_ecoscheme_classification()}\n</classification>\n\n{cap_form_instructions}"

    # The mapping and amounts are precomputed here: the LLM may only narrate
    # them, never recompute or adjust a figure.
    user_payload = (
        f"User Request: {_last_user_text(messages)}\n\n"
        f"<pending_action>{pending_action or 'NONE'}</pending_action>\n\n"
        f"<crop_metadata>\n"
        f"{json.dumps(crop_metadata, ensure_ascii=False, indent=2) if crop_metadata else 'No crop metadata available.'}\n"
        f"</crop_metadata>\n\n"
        f"<cap_form_data>\n{json.dumps(slots, ensure_ascii=False, indent=2)}\n</cap_form_data>\n\n"
        f"<form_mapping>\n{json.dumps(mapping, ensure_ascii=False, indent=2)}\n</form_mapping>\n\n"
        f"<estimated_amounts>\n{json.dumps(amounts, ensure_ascii=False, indent=2)}\n</estimated_amounts>\n\n"
        f"<assessment_report>\n{assessment_report or 'No assessment report available.'}\n</assessment_report>\n\n"
        "Report the estimated amounts exactly as given in <estimated_amounts>. "
        "Do not calculate, round differently, or introduce any figure that is not present there."
    )

    chat = LocalChat(
        client=client,
        model_name=model_name,
        system_instruction=system_instruction,
        history_init=get_recent_history(messages[:-1], 4),
        max_context_tokens=APPLICATION_CONTEXT_TOKENS,
    )
    response = chat.send_message(user_payload)

    update["messages"] = [AIMessage(content=getattr(response, "text", str(response)))]
    return update
