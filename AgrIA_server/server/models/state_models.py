from typing import TypedDict, Optional
from langchain_core.messages import BaseMessage


# Define the clean State representation for LangGraph
class AgrIAState(TypedDict):
    messages: list[BaseMessage]
    lang: str  # "es" or "en"
    crop_metadata: dict  # The JSON calculated from your ES tools
    visual_description: Optional[str]
