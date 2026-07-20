import re
import structlog

from ..config.constants import BASE_PROMPTS_PATH
from ..models.chat_models import LocalChat
from ..models.state_models import AgrIAState

logger = structlog.get_logger(__file__)

domain_vocabulary = {
  "es": ["parcela", "cultivo", "sigpac", "catastro", "subvencion", "pac", "ecorregimen", "tierra"],
  "en": ["parcel", "crop", "sigpac", "cadastral", "subsidy", "cap", "ecoscheme", "farmland", "agriculture"]
}

def load_prompt_asset(lang: str, filename: str) -> str:
    """Reads modular markdown text prompts directly from filesystem."""
    file_path = BASE_PROMPTS_PATH / lang / filename
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        # Fallback block to prevent server crash
        return "You are AgrIA, an agricultural AI chatbot assistant."

# 2. Node Functions
def execute_scoped_chat(state: AgrIAState, client, model_name: str, prompt_filename: str, get_lang: bool = True) -> dict:
    """Core underlying utility handler to process stateless conversational nodes."""
    lang = state.get("lang", "es") if get_lang else ""
    user_input = state["messages"][-1].content

    # Dynamically pull the file asset (e.g., 'ROLE.md' or 'FALLBACK.md')
    system_instruction = load_prompt_asset(lang, prompt_filename)
    
    chat = LocalChat(
        client=client, 
        model_name=model_name, 
        system_instruction=system_instruction,
        max_context_tokens=8000
    )
    
    response_wrapper = chat.send_message(user_input)
    return {
        "messages": state["messages"] + [response_wrapper.text]
    }

def basic_chat_node(state: AgrIAState, client, model_name: str) -> dict:
    return execute_scoped_chat(state, client, model_name, "ROLE.md", False)

def fallback_rejection_node(state: AgrIAState, client, model_name: str) -> dict:
    return execute_scoped_chat(state, client, model_name, "FALLBACK.md", False)

# 3. Deterministic Routing Controller
def deterministic_router(state: AgrIAState) -> str:
    """Evaluates text patterns deterministically before running an LLM routing token round."""
    if not state["messages"]:
        logger.debug(f"BASIC CHAT 0 DETECTED")
        return "basic_chat"
        
    last_message = state["messages"][-1]
    text_content = str(last_message.content).lower().strip()
    
    # Check 1: Direct feature triggers
    if "###describe_short_image###" in text_content:
        logger.debug(f"REPORT GENERATION DETECTED")
        return "report_generator"
        
    # Check 2: Simple text matches via regex rules
    greetings = r"\b(hola|buenos dias|buenas tardes|hi|hello|hey|quien eres|who are you)\b"
    if re.search(greetings, text_content):
        logger.debug(f"BASIC CHAT 1 DETECTED")
        return "basic_chat"
        
    # Check 3: Check agricultural scope keyword domain list
    active_keywords = domain_vocabulary.get(state.get("lang", "es"), [])
    if any(kw in text_content for kw in active_keywords):
        logger.debug(f"BASIC CHAT 2 DETECTED")
        return "basic_chat"
        
    # Default condition if context falls outside domain bounds
    logger.debug(f"FALLBACK CHAT DETECTED")
    return "fallback_rejection"
