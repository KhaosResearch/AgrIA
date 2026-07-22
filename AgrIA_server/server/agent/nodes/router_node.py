import re
import structlog

from ...models.state_models import AgrIAState

logger = structlog.get_logger(__file__)

domain_vocabulary = {
    "es": [
        "parcela",
        "cultivo",
        "sigpac",
        "catastro",
        "subvencion",
        "pac",
        "ecorregimen",
        "tierra",
    ],
    "en": [
        "parcel",
        "crop",
        "sigpac",
        "cadastral",
        "subsidy",
        "cap",
        "ecoscheme",
        "farmland",
        "agriculture",
    ],
}


def deterministic_router(state: AgrIAState) -> str:
    """Evaluates text patterns deterministically before running an LLM routing token round."""
    if not state["messages"]:
        logger.debug(f"BASIC CHAT 0 DETECTED")
        return "basic_chat"

    last_message = state["messages"][-1]
    text_content = str(last_message.content).lower().strip()

    if "###describe_short_image###" in text_content:
        logger.debug(f"REPORT GENERATION DETECTED")
        return "report_generator"

    cap_keywords = ["ecorregimen", "ecorregímenes", "pac", "subvencion", "subvenciones", "ayuda", "requisitos"]
    if any(kw in text_content for kw in cap_keywords):
        return "cap_query"

    greetings = (
        r"\b(hola|buenos dias|buenas tardes|hi|hello|hey|quien eres|who are you)\b"
    )
    if re.search(greetings, text_content):
        logger.debug(f"BASIC CHAT 1 DETECTED")
        return "basic_chat"

    active_keywords = domain_vocabulary.get(state.get("lang", "es"), [])
    if any(kw in text_content for kw in active_keywords):
        logger.debug(f"BASIC CHAT 2 DETECTED")
        return "basic_chat"
        
    # Default condition if context falls outside domain bounds
    logger.debug(f"FALLBACK CHAT DETECTED")
    return "fallback_rejection"
