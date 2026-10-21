import structlog

from langchain_core.messages import HumanMessage, AIMessage

from ..config.constants import BASE_PROMPTS_PATH
from ..models.chat_models import LocalChat
from ..models.state_models import AgrIAState
from ..utils.chat_utils import get_recent_history

logger = structlog.get_logger(__file__)


def load_prompt_asset(filename: str, lang: str = "") -> str:
    """Reads modular markdown text prompts directly from filesystem.

    Raises `FileNotFoundError` when the asset is missing. A silent fallback to a
    generic chatbot instruction would hide typos in prompt names and quietly
    degrade node behaviour, so the failure must surface.
    """
    file_path = BASE_PROMPTS_PATH / lang / filename
    return file_path.read_text(encoding="utf-8")


def execute_scoped_chat(
    state: AgrIAState,
    client,
    model_name: str,
    prompt_filename: str,
    get_lang: bool = True,
) -> dict:
    """Core underlying utility handler to process stateless conversational nodes."""
    lang = state.get("lang", "es") if get_lang else ""
    last_chat_msg = state["messages"][-1]

    if type(last_chat_msg) is HumanMessage:
        user_input = last_chat_msg.content

        system_instruction = load_prompt_asset(prompt_filename, lang)

        chat = LocalChat(
            client=client,
            model_name=model_name,
            system_instruction=system_instruction,
            history_init=get_recent_history(state["messages"][:-1]),
            max_context_tokens=25000,
        )

        response_wrapper = chat.send_message(user_input)
        out = {"messages": state["messages"] + [AIMessage(response_wrapper.text)]}
    else:
        logger.warning(
            "Detected chat message was not from the user. Skipping node interaction..."
        )
        out = {"messages": state["messages"]}

    return out
