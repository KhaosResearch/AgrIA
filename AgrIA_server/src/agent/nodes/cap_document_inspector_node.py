import json
import structlog

from langchain_core.messages import AIMessage, HumanMessage
from typing import Any, Dict, Optional

from ...models.chat_models import LocalChat
from ...models.state_models import AgrIAState
from ...utils.cap_form_utils import load_cap_slots, normalise_slots
from ...utils.chat_utils import get_recent_history
from ...utils.nodes_utils import load_prompt_asset

logger = structlog.get_logger(__name__)

INSPECTOR_CONTEXT_TOKENS = 25000


def _pdf_path_from(content: Any) -> Optional[str]:
    """Best-effort discovery of an uploaded PDF path in a multimodal message.

    Accepts a bare string path, a multimodal part list, or a dict carrying a
    `file`/`document`/`file_path` key. Returns None when nothing looks like a
    PDF, so the caller can fall back to text clarification.
    """
    candidates: list[Any] = []

    if isinstance(content, str):
        candidates.append(content)
    elif isinstance(content, list):
        for part in content:
            if isinstance(part, dict):
                candidates.extend(
                    part.get(key)
                    for key in ("file_path", "path", "file", "document", "url")
                )
            elif isinstance(part, str):
                candidates.append(part)
    elif isinstance(content, dict):
        candidates.extend(
            content.get(key) for key in ("file_path", "path", "file", "document", "url")
        )

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.lower().endswith(".pdf"):
            return candidate
    return None


def _read_pdf_text(path: str) -> str:
    """Extract plain text from a PDF. Empty string when unreadable."""
    try:
        from ...scripts.schema_extraction import extract_pdf_text

        return extract_pdf_text(path)
    except Exception as exc:  # unreadable/encrypted/scanned PDF
        logger.warning("cap_pdf_text_extraction_failed", path=path, error=str(exc))
        return ""


def _schema_block() -> str:
    """Field list handed to the extractor so it can only emit known slots."""
    schema, _ = load_cap_slots()
    return "\n".join(
        f"- {name} (type={spec['type']}"
        f"{', enum=' + '|'.join(spec['enum']) if spec.get('enum') else ''})"
        for name, spec in schema.items()
    )


def _parse_slots(text: str) -> dict:
    """Parse the extractor's JSON object, tolerating code fences."""
    if not text:
        return {}
    candidate = text.strip()
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


def cap_document_inspector_node(
    state: AgrIAState, client, model_name: str
) -> Dict[str, Any]:
    """LangGraph Node: extract CAP slots from an uploaded PDF.

    Extracted values land in `cap_alignment["slots"]`, the same structure the
    free-text guard produces, so both clarification paths converge in
    `cap_application_node`. Nothing is written to `cap_form_data` here, and a
    field the document does not state is simply absent — never invented.
    """
    messages = state.get("messages", [])
    current = messages[-1] if messages else None
    if not isinstance(current, HumanMessage):
        return {"cap_alignment": None}

    pdf_path = _pdf_path_from(current.content)
    if not pdf_path:
        return {"cap_alignment": None}

    document_text = _read_pdf_text(pdf_path)
    if not document_text.strip():
        # A scanned or unreadable PDF must not stall the workflow: ask for text.
        lang = state.get("lang", "es")
        if lang == "en":
            content = (
                "I could not read text from that PDF, so I have not filled in any "
                "field. Please send the key details as text: NIF/CIF, your name, "
                "IBAN, parcel ID, crop, surface in hectares, irrigation type and "
                "the aid lines you are applying for."
            )
        else:
            content = (
                "No he podido leer el texto de ese PDF, así que no he rellenado "
                "ningún campo. Envíame los datos clave en texto: NIF/CIF, nombre, "
                "IBAN, referencia catastral, cultivo, superficie en hectáreas, tipo "
                "de regadío y las líneas de ayuda solicitados."
            )
        return {
            "cap_workflow": "collect",
            "messages": [AIMessage(content=content)],
        }

    lang = state.get("lang", "es")
    system_instruction = (
        f"{load_prompt_asset('CAP_SLOT_GUARD.md')}\n\n"
        "In this task you are reading an official CAP application document, not a "
        "farmer's chat message. Extract every field the document explicitly "
        "states. Use a field name only if it appears in <allowed_fields>."
    )
    user_payload = (
        f"<allowed_fields>\n{_schema_block()}\n</allowed_fields>\n\n"
        f"<document>\n{document_text}\n</document>\n\n"
        'Output {"classification": "answer", "confidence": 1.0, "slots": {...}, "reason": "..."} '
        "with only the fields the document explicitly states. Leave out anything "
        "not stated; never infer or calculate a value."
    )

    chat = LocalChat(
        client=client,
        model_name=model_name,
        system_instruction=system_instruction,
        history_init=get_recent_history(messages[:-1], 4),
        max_context_tokens=INSPECTOR_CONTEXT_TOKENS,
    )

    try:
        response = chat.send_message(user_payload)
        verdict = _parse_slots(getattr(response, "text", str(response)))
        # The extractor answers with the guard's verdict shape, so the values
        # live under "slots"; parsing the wrapper directly would drop them all.
        proposed = (
            verdict.get("slots") if isinstance(verdict.get("slots"), dict) else verdict
        )
        slots = normalise_slots(proposed)
    except Exception as exc:  # defensive: transport/provider failure
        logger.warning("cap_pdf_extraction_failed", path=pdf_path, error=str(exc))
        return {"cap_alignment": None}

    logger.info(
        "cap_pdf_slots_extracted", count=len(slots), fields=sorted(slots.keys())
    )

    found = len(slots)
    if lang == "en":
        confirmation = (
            f"I read {found} field(s) from your document: {', '.join(sorted(slots))}. "
            if found
            else "I could not identify any CAP fields in that document. "
        )
    else:
        confirmation = (
            f"He leído {found} dato(s) de tu documento: {', '.join(sorted(slots))}. "
            if found
            else "No he identificado ningún dato de la solicitud CAP en ese documento. "
        )

    return {
        "cap_alignment": {
            "classification": "answer",
            "confidence": 1.0,
            "slots": slots,
            "reason": f"extracted from {pdf_path}",
        },
        "cap_workflow": "collect",
        "messages": [AIMessage(content=confirmation)],
    }
