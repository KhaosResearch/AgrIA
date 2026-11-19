import json
import structlog

from typing import Literal

from ...models.chat_models import LocalChat
from ...models.state_models import AgrIAState, INTENT_REGISTRY
from ...utils.chat_utils import get_recent_history
from ...utils.nodes_utils import load_prompt_asset

logger = structlog.get_logger(__name__)

# Backwards-compatible alias. The canonical set lives in `state_models`
# (`INTENT_REGISTRY`) so the graph edge map and the classifier share one source.
VALID_INTENTS = Literal[tuple(INTENT_REGISTRY)]  # type: ignore[valid-type]

# A pending CAP slot question outranks every other intent: the farmer is
# answering a field, so the message must reach the guard, not the LLM router.
CAP_SLOT_PREFIX = "AWAITING_SLOT:"

# Below this classifier confidence we do not trust a single label: the turn is
# routed to `basic_chat`, which is instructed to ask one clarifying question
# instead of guessing. This turns a silent misroute into a recoverable one.
ROUTER_CONFIDENCE_THRESHOLD = 0.55


def _log_routing(
    source: str,
    primary: str,
    confidence: float | None,
    secondary: str | None = None,
    **extra,
) -> None:
    """Single telemetry point for every routing decision.

    A misroute used to be invisible: the model could return `basic_chat` and the
    classifier could crash, and both looked identical downstream. Logging the
    source (fast-path vs llm vs fallback), the confidence and any secondary
    intent makes every decision auditable and gives the eval harness a hook.
    """
    logger.info(
        "router_decision",
        source=source,
        primary=primary,
        confidence=confidence,
        secondary=secondary,
        **extra,
    )


def _clarification_message(lang: str) -> str:
    """Bilingual nudge used when the classifier is not confident enough."""
    if lang == "en":
        return (
            "I want to make sure I help you with the right thing. Could you tell me "
            "whether you'd like to (a) check the rules or requirements of an "
            "eco-scheme, (b) find out the payment rates, (c) start or continue "
            "filling in your CAP application, or (d) generate a parcel report?"
        )
    return (
        "Quiero asegurarme de ayudarte con lo correcto. ¿Podrías indicarme si quieres "
        "(a) consultar las normas o requisitos de un ecorregímen, (b) conocer los "
        "importes de pago, (c) empezar o continuar rellenando tu solicitud CAP, o "
        "(d) generar un informe de tu parcela?"
    )


def _parse_router_json(response_text: str) -> dict:
    """Extract the router JSON object, tolerating code fences and prose."""
    candidate = response_text.strip()
    if candidate.startswith("```"):
        candidate = candidate.split("```")[1]
        if candidate.lstrip().lower().startswith("json"):
            candidate = candidate.lstrip()[4:]
    start, end = candidate.find("{"), candidate.rfind("}")
    if start == -1 or end <= start:
        return {}
    try:
        parsed = json.loads(candidate[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _valid_intent(value: object) -> str | None:
    """Return `value` if it is a known intent, else None (single source check)."""
    if isinstance(value, str) and value in INTENT_REGISTRY:
        return value
    return None


def deterministic_router(state: AgrIAState, client, model_name: str) -> str:
    """
    Hybrid Graph Router:
    1. Fast-Path: Resumable CAP workflows and explicit system tags (zero LLM cost).
    2. LLM Intent Classifier: Evaluates natural language phrasing via structured JSON.

    Returns the node name to run. On the LLM path, a detected second intent is
    stored in `state["secondary_intent"]` so the primary node can also address it —
    multi-intent without any topology change.
    """
    messages = state.get("messages", [])
    if not messages:
        _log_routing("empty", "basic_chat", None)
        return "basic_chat"

    pending_action = state.get("pending_action") or ""

    # The guard decides whether the message answers the pending field or shifts
    # topic; routing is deterministic and language-agnostic by construction.
    if pending_action.startswith(CAP_SLOT_PREFIX):
        _log_routing("fast_path", "cap_slot_guard", 1.0, slot=pending_action)
        return "cap_slot_guard"

    last_msg = messages[-1]
    text_content = str(last_msg.content).strip()

    # Fast-Path 1: Empty input check
    if not text_content:
        _log_routing("fast_path", "basic_chat", 1.0)
        return "basic_chat"

    # Fast-Path 2: System tag check for report generation (both variants)
    if "###DESCRIBE_SHORT_IMAGE###" in text_content or "###DESCRIBE_LONG_IMAGE###" in text_content:
        _log_routing("fast_path", "report_generator", 1.0)
        return "report_generator"

    # Fallback: LLM Intent Classifier
    try:
        system_instruction = load_prompt_asset("INTENT.md")

        classifier_chat = LocalChat(
            client=client,
            model_name=model_name,
            system_instruction=system_instruction,
            history_init=get_recent_history(messages[:-1], max_turns=6),
            max_context_tokens=25000,
        )

        user_prompt = (
            f"Classify the intent of the last message in this context:\n"
            f"<last_user_message>\n{text_content}\n</last_user_message>"
        )

        response_wrapper = classifier_chat.send_message(user_prompt)
        data = _parse_router_json(response_wrapper.text)

        primary = _valid_intent(data.get("intent"))
        if primary is None:
            # Unknown label: treat as a low-signal turn rather than a valid route.
            _log_routing(
                "llm_invalid", "basic_chat", None, raw=str(data.get("intent"))
            )
            state["secondary_intent"] = None
            return "basic_chat"

        try:
            confidence = float(data.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        # Secondary intent: only kept when valid and different from the primary.
        secondary = _valid_intent(data.get("secondary_intent"))
        if secondary == primary:
            secondary = None

        _log_routing("llm", primary, confidence, secondary=secondary)

        if confidence < ROUTER_CONFIDENCE_THRESHOLD:
            # Not confident enough to commit to a label: ask, don't guess.
            state["secondary_intent"] = None
            return "clarify"

        state["secondary_intent"] = secondary
        return primary

    except Exception as e:
        # Distinguish a crash from a low-confidence verdict in the logs.
        logger.warning("router_classifier_failed", error=str(e))
        _log_routing("llm_error", "basic_chat", None, error=str(e))
        state["secondary_intent"] = None
        return "basic_chat"


def clear_cap_workflow(state: AgrIAState) -> dict:
    """LangGraph Node: drop a CAP workflow when the farmer changes topic.

    Replaces the previous in-place `state["pending_action"] = None`, which never
    reached the checkpointer and so could not actually resume or clear anything.
    """
    logger.info("cap_workflow_cleared", pending_action=state.get("pending_action"))
    return {"pending_action": None, "cap_workflow": None, "cap_alignment": None}


def cap_guard_edge(state: AgrIAState) -> str:
    """Separate interruption intents from normal CAP field extraction.

    Returns one of: "cap_interruption", "cap_application", "clear_cap_workflow".
    The cancel classification routes to `clear_cap_workflow` so the node is
    actually reachable in the graph (it was previously dead code).
    """

    alignment = state.get("cap_alignment") or {}
    classification = alignment.get("classification")

    if classification == "cancel":
        return "clear_cap_workflow"

    if classification in {"topic_change", "pause", "resume"}:
        return "cap_interruption"

    return "cap_application"
