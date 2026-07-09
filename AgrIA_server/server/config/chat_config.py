
from google.genai import types

from .constants import MODEL_NAME
from .llm_client import client
from ..models.chat import LocalChat
from ..utils.llm_utils import generate_system_instructions, set_initial_history


def create_chat():
    chat = LocalChat.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=generate_system_instructions()
        ),
        history=set_initial_history(),
    )
    return chat


CHAT = create_chat() if client else None
# CHAT = None
