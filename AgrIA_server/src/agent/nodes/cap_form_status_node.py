"""Deterministic node: show the current state of the CAP application form.

No LLM call: the farmer asks "show me my form" / "what have I filled in" and
gets a structured summary of the collected slots, the outstanding question,
and the workflow status. This closes the gap where the farmer could not
inspect their own progress mid-application.
"""

import structlog
from langchain_core.messages import AIMessage

from ...models.state_models import AgrIAState
from ...utils.cap_form_utils import load_cap_slots

logger = structlog.get_logger(__name__)

# Friendly display names for the most common slots. Unknown slots fall back
# to the schema question text (truncated) or the raw key.
_SLOT_LABELS = {
    "beneficiary.nif_cif": "NIF/CIF",
    "beneficiary.full_name": "Nombre completo",
    "beneficiary.iban": "IBAN",
    "parcels[].parcel_id": "Referencia de parcela",
    "parcels[].declared_crop": "Cultivo declarado",
    "parcels[].declared_surface_ha": "Superficie (ha)",
    "parcels[].irrigation_type": "Tipo de riego",
    "requested_aid_lines": "Líneas de ayuda solicitadas",
}


def _slot_label(name: str, slot_defs: dict) -> str:
    """Human-readable label for a slot key."""
    if name in _SLOT_LABELS:
        return _SLOT_LABELS[name]
    definition = slot_defs.get(name)
    if definition and definition.get("question_es"):
        # Use the first sentence of the question as a label.
        return definition["question_es"].split(".")[0].split("?")[0][:60]
    return name


def cap_form_status_node(state: AgrIAState) -> dict:
    """Return a deterministic summary of the CAP form state.

    Terminal node: no LLM, no state mutation (except clearing
    `secondary_intent`). The farmer sees exactly what has been collected,
    what is still missing, and the current workflow status.
    """
    lang = state.get("lang", "es")
    form_data = state.get("cap_form_data") or {}
    pending_action = state.get("pending_action") or ""
    cap_workflow = state.get("cap_workflow") or "none"

    slot_defs = load_cap_slots()[0] if load_cap_slots() else {}

    if not form_data and cap_workflow in ("none", "cancelled"):
        if lang == "en":
            msg = (
                "You have not started a CAP application yet. "
                "Say 'I want to apply for eco-schemes' to begin."
            )
        else:
            msg = (
                "Aún no has iniciado una solicitud CAP. "
                "Di «quiero solicitar los ecorregímenes» para empezar."
            )
        return {
            "messages": [AIMessage(content=msg)],
            "secondary_intent": None,
        }

    # Build the summary table
    lines = []
    if lang == "en":
        lines.append("**Your CAP application so far:**")
    else:
        lines.append("**Tu solicitud CAP hasta ahora:**")

    for key, value in form_data.items():
        label = _slot_label(key, slot_defs)
        if isinstance(value, list):
            display = ", ".join(str(v) for v in value)
        else:
            display = str(value)
        lines.append(f"- **{label}**: {display}")

    # Pending question
    if pending_action.startswith("AWAITING_SLOT:"):
        slot_name = pending_action.split(":", 1)[1]
        pending_label = _slot_label(slot_name, slot_defs)
        if lang == "en":
            lines.append(f"\n**Outstanding:** {pending_label}")
        else:
            lines.append(f"\n**Pendiente:** {pending_label}")

    # Workflow status
    status_map = {
        "collect": "in progress" if lang == "en" else "en curso",
        "paused": "paused" if lang == "en" else "en pausa",
        "ready": "complete — ready to submit"
        if lang == "en"
        else "completa — lista para enviar",
        "cancelled": "cancelled" if lang == "en" else "cancelada",
    }
    status_text = status_map.get(cap_workflow, cap_workflow)
    if lang == "en":
        lines.append(f"\n**Status:** {status_text}")
    else:
        lines.append(f"\n**Estado:** {status_text}")

    if lang == "en":
        lines.append(
            "\nYou can continue by answering the outstanding field, "
            "or say 'pause' / 'cancel' if you need to."
        )
    else:
        lines.append(
            "\nPuedes continuar respondiendo al campo pendiente, "
            "o decir «pausa» / «cancelar» si lo necesitas."
        )

    content = "\n".join(lines)
    logger.info("cap_form_status", fields=len(form_data), status=cap_workflow)
    return {
        "messages": [AIMessage(content=content)],
        "secondary_intent": None,
    }
