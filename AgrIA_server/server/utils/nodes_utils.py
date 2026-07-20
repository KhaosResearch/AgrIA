import structlog

from ..config.constants import BASE_PROMPTS_PATH
from ..models.chat_models import LocalChat
from ..models.state_models import AgrIAState

logger = structlog.get_logger(__file__)


def load_prompt_asset(lang: str, filename: str) -> str:
    """Reads modular markdown text prompts directly from filesystem."""
    file_path = BASE_PROMPTS_PATH / lang / filename
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        # Fallback block to prevent server crash
        return "You are AgrIA, an agricultural AI chatbot assistant."


def execute_scoped_chat(
    state: AgrIAState,
    client,
    model_name: str,
    prompt_filename: str,
    get_lang: bool = True,
) -> dict:
    """Core underlying utility handler to process stateless conversational nodes."""
    lang = state.get("lang", "es") if get_lang else ""
    user_input = state["messages"][-1].content

    system_instruction = load_prompt_asset(lang, prompt_filename)

    chat = LocalChat(
        client=client,
        model_name=model_name,
        system_instruction=system_instruction,
        max_context_tokens=8000,
    )

    response_wrapper = chat.send_message(user_input)
    return {"messages": state["messages"] + [response_wrapper.text]}
