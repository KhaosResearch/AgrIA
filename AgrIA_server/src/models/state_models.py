from typing import TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing import Annotated

# Define the clean State representation for LangGraph
class AgrIAState(TypedDict):
    messages: Annotated[BaseMessage, add_messages]
    lang: str  # "es" or "en"
    crop_metadata: dict  # The JSON calculated from your ES tools
    visual_description: Optional[str]
    correction_feedback: Optional[str]
