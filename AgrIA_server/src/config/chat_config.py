from langchain_core.messages import BaseMessage

from .config import LLM_MODEL_NAME
from .llm_client import client
from ..models.chat_models import LocalChat
from ..utils.llm_utils import generate_system_instructions, set_initial_history


def create_chat(
    llm_client=client,
    model_name: str = LLM_MODEL_NAME,
    system_instruction: str = None,
    chat_history: list[BaseMessage] = None,
):
    sys_instruction = (
        generate_system_instructions()
        if system_instruction is None
        else system_instruction
    )
    chat_history = set_initial_history() if chat_history is None else chat_history

    chat = LocalChat(
        client=llm_client,
        model_name=model_name,
        system_instruction=sys_instruction,
        history_init=chat_history,
    )
    return chat


CHAT = create_chat() if client else None
# CHAT = None
