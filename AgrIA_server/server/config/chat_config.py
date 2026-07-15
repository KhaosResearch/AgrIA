from .config import LLM_MODEL_NAME

from .llm_client import client
from ..models.chat_models import LocalChat
from ..utils.llm_utils import generate_system_instructions, set_initial_history


def create_chat():
    chat = LocalChat(
        client=client,
        model_name=LLM_MODEL_NAME,
        system_instruction=generate_system_instructions(),
        history_init=set_initial_history(),  # Adjust if format mismatch occurs
    )
    return chat


CHAT = create_chat() if client else None
# CHAT = None
