import json
import structlog

from langchain_core.messages import HumanMessage
from typing import Any, Dict, Optional

from ...models.chat_models import LocalChat
from ...models.state_models import AgrIAState
from ...utils.cap_form_utils import load_cap_slots, normalise_slots, slot_definition
from ...utils.chat_utils import get_recent_history
from ...utils.nodes_utils import load_prompt_asset

logger = structlog.get_logger(__name__)

# Only these verdicts let the CAP workflow advance; anything else keeps us
# collecting so an unrelated message never gets written into the form.
ACCEPTED_CLASSIFICATIONS = {"answer", "correction", "missing_information"}
VALID_CLASSIFICATIONS = ACCEPTED_CLASSIFICATIONS | {"topic_change"}

GUARD_CONTEXT_TOKENS = 4000

# The guard is a short, constrained JSON reply, so a malformed one is a rare
# provider-side glitch rather than a signal about the user. One retry recovers
# almost all of those without adding a second call to the normal path.
GUARD_MAX_ATTEMPTS = 2


def _schema_block(
    slots: Optional[dict], pending_action: Optional[str], lang: str
) -> str:
    """Bilingual schema + current-state block fed to the guard."""
    schema, _ = load_cap_slots()
    question_key = "question_en" if lang == "en" else "question_es"
    alias_key = "aliases_en" if lang == "en" else "aliases_es"

    lines = [
        f"<current_slots>\n{json.dumps(slots or {}, ensure_ascii=False)}</current_slots>",
        f"<awaiting>{pending_action or 'none'}</awaiting>",
        "<allowed_fields>",
    ]
    for name, spec in schema.items():
        enum = spec.get("enum")
        lines.append(
            f"- {name} | type={spec['type']} | required={spec['required']}"
            f" | enum={'|'.join(enum) if enum else '-'}"
            f" | asks={spec[question_key]}"
            f" | aliases={','.join(spec.get(alias_key) or []) or '-'}"
        )
    lines.append("</allowed_fields>")
    return "\n".join(lines)


def _parse_verdict(text: str) -> Optional[dict]:
    """Extract the guard JSON from a model reply, tolerating code fences."""
    if not text:
        return None
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate.split("```")[1]
        if candidate.lstrip().lower().startswith("json"):
            candidate = candidate.lstrip()[4:]
    start, end = candidate.find("{"), candidate.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(candidate[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _fallback_alignment(state: AgrIAState, user_text: str) -> Dict[str, Any]:
    """Classify a reply deterministically when the guard returns no usable JSON.

    Only the slot named by ``pending_action`` is considered, and it still has to
    survive `normalise_slots`, so a malformed value or an off-topic sentence is
    rejected here just as it would be by the model. An unrecognised reply is
    treated as a topic change so the form is never polluted.
    """
    name = pending_slot_name(state.get("pending_action"))
    slots = normalise_slots({name: user_text}) if name else {}
    if not slots:
        return {
            "cap_alignment": {
                "classification": "topic_change",
                "confidence": 0.0,
                "slots": {},
                "reason": "guard returned no JSON and the text did not validate",
            }
        }
    logger.info("cap_slot_guard_fallback", slot=name)
    return {
        "cap_alignment": {
            "classification": "answer",
            "confidence": 0.5,
            "slots": slots,
            "reason": f"accepted for pending slot {name} without classifier JSON",
        }
    }


def cap_slot_guard_node(
    state: AgrIAState, client: Any, model_name: str
) -> Dict[str, Any]:
    """LangGraph Node: one cheap, tightly constrained LLM call that both
    classifies the user's reply and extracts any CAP slots it contains.

    Replaces the English keyword topic-shift list so relevance detection also
    works in Spanish and for paraphrased replies. Slot values are schema-gated
    here; `cap_application_node` remains the only writer of `cap_form_data`.
    """
    messages = state.get("messages", [])
    if not messages or not isinstance(messages[-1], HumanMessage):
        return {"cap_alignment": None}

    user_text = str(messages[-1].content)
    if not user_text.strip():
        return {
            "cap_alignment": {
                "classification": "missing_information",
                "confidence": 0.0,
                "slots": {},
                "reason": "empty message",
            }
        }

    lang = state.get("lang", "es")
    system_instruction = load_prompt_asset("CAP_SLOT_GUARD.md")
    user_payload = (
        f"{_schema_block(state.get('cap_form_data'), state.get('pending_action'), lang)}\n\n"
        f"<user_message>\n{user_text}\n</user_message>"
    )

    chat = LocalChat(
        client=client,
        model_name=model_name,
        system_instruction=system_instruction,
        history_init=get_recent_history(messages[:-1], 4),
        max_context_tokens=GUARD_CONTEXT_TOKENS,
    )

    verdict: Optional[dict] = None
    for attempt in range(GUARD_MAX_ATTEMPTS):
        try:
            response = chat.send_message(user_payload)
            raw = getattr(response, "text", str(response))
            verdict = _parse_verdict(raw)
        except Exception as exc:  # defensive: transport/provider failure
            logger.warning("cap_slot_guard_failed", error=str(exc))
            return {"cap_alignment": None}

        if verdict is not None:
            break
        logger.warning("cap_slot_guard_unparseable", attempt=attempt + 1)

    if verdict is None:
        # Never drop what the farmer typed just because the classifier misfired:
        # fall back to accepting the raw text for the single field we are
        # actually waiting on, still gated by the schema validator.
        return _fallback_alignment(state, user_text)

    classification = str(verdict.get("classification", "")).strip()
    if classification not in VALID_CLASSIFICATIONS:
        # Unknown label -> assume the message is off-topic rather than collecting noise.
        classification = "topic_change"
    try:
        confidence = float(verdict.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    # Schema gate: fields outside the versioned schema, and unparseable values, are dropped.
    slots = normalise_slots(verdict.get("slots"))

    alignment = {
        "classification": classification,
        "confidence": max(0.0, min(1.0, confidence)),
        "slots": slots,
        "reason": str(verdict.get("reason", ""))[:200],
    }
    logger.info(
        "cap_slot_guard",
        classification=classification,
        slots=sorted(slots.keys()),
    )
    return {"cap_alignment": alignment}


def pending_slot_name(pending_action: Optional[str]) -> Optional[str]:
    """Extract the slot name from an ``AWAITING_SLOT:<name>`` marker."""
    if not pending_action or not pending_action.startswith("AWAITING_SLOT:"):
        return None
    name = pending_action.split(":", 1)[1].strip()
    return name or None


def next_slot_prompt(pending_action: Optional[str], lang: str = "es") -> str:
    """Bilingual question for the slot the graph is currently waiting on."""
    name = pending_slot_name(pending_action)
    if not name:
        return ""
    spec = slot_definition(name)
    if not spec:
        return ""
    return spec["question_en"] if lang == "en" else spec["question_es"]


def topic_change_message(lang: str = "es") -> str:
    """Reply used when the user has clearly changed topic."""
    if lang == "en":
        return (
            "It looks like this message is not about your CAP application, so I "
            "have not changed any field. Your CAP application is still in progress."
        )
    return (
        "Parece que este mensaje no trata sobre tu solicitud CAP, así que no he "
        "modificado ningún campo. Tu solicitud CAP sigue en curso."
    )


def acknowledgement_message(lang: str = "es") -> str:
    """Reply used to confirm accepted slot values, without inventing amounts."""
    if lang == "en":
        return "Noted, I have updated the following fields in your CAP application: "
    return "Entendido, he actualizado los siguientes campos de tu solicitud CAP: "


def summarise_slots(slots: Optional[dict], names: list[str]) -> str:
    """Human-readable confirmation of the slots that were just written."""
    parts = []
    for name in names:
        value = (slots or {}).get(name)
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        parts.append(f"- {name}: {value}")
    return "\n".join(parts) + ("\n" if parts else "")


def guard_ack(slots: Optional[dict], names: list[str], lang: str = "es") -> str:
    """Confirm the slot values just written, without inventing any figure."""
    if not names:
        return ""
    return f"{acknowledgement_message(lang)}{summarise_slots(slots, names)}"
