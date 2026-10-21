from typing import Any, Dict

from langchain_core.messages import AIMessage

from ...models.state_models import AgrIAState
from .basic_chat_node import basic_chat_node
from .cap_application_node import cap_application_node


def cap_interruption_node(
    state: AgrIAState,
    client: Any,
    model_name: str,
) -> Dict[str, Any]:
    """Handle CAP interruptions without mixing them into form extraction."""

    alignment = state.get("cap_alignment") or {}
    classification = alignment.get("classification")
    lang = state.get("lang", "es")

    # Consume the guard result: never reapply its slots on a later turn.
    clear_alignment = {"cap_alignment": None}

    if classification == "pause":
        return {
            **clear_alignment,
            "cap_workflow": "paused",
            # Preserve cap_form_data and pending_action.
            "messages": [
                AIMessage(
                    content=(
                        "Your CAP application is paused. Your collected information "
                        "has been preserved. Say 'resume' whenever you're ready."
                        if lang == "en"
                        else "Tu solicitud CAP está en pausa. He conservado la "
                        "información recopilada. Di «continuar» cuando quieras "
                        "retomarla."
                    )
                )
            ],
        }

    if classification == "cancel":
        return {
            **clear_alignment,
            "cap_workflow": "cancelled",
            "cap_form_data": None,
            "pending_action": None,
            "messages": [
                AIMessage(
                    content=(
                        "Your CAP application has been cancelled. Your collected "
                        "form data has been cleared from the active application. "
                        "You can start again whenever you wish."
                        if lang == "en"
                        else "Tu solicitud CAP se ha cancelado. He borrado los datos "
                        "recopilados del formulario activo. Puedes empezar de "
                        "nuevo cuando quieras."
                    )
                )
            ],
        }

    if classification == "resume":
        # Re-enter the existing validation/collection logic. Do not interpret
        # the word "resume" as the value of the outstanding field.
        resumed_state = {
            **state,
            "cap_alignment": None,
            "cap_workflow": "collect",
        }
        return cap_application_node(resumed_state, client, model_name)

    if classification == "topic_change":
        # Answer normally while leaving the CAP form and pending action intact.
        response = basic_chat_node(state, client, model_name)
        return {
            **response,
            **clear_alignment,
        }

    # Defensive fallback: do not mutate the form on an unknown intent.
    return {
        **clear_alignment,
        "messages": [
            AIMessage(
                content=(
                    "I couldn't determine how you'd like to proceed. You can "
                    "answer the pending question, ask something else, pause, "
                    "or cancel the application."
                    if lang == "en"
                    else "No he podido determinar cómo quieres continuar. Puedes "
                    "responder a la pregunta pendiente, consultar otro tema, "
                    "poner la solicitud en pausa o cancelarla."
                )
            )
        ],
    }
