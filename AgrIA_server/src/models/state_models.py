from typing import TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing import Annotated


# Define the clean State representation for LangGraph
class AgrIAState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    lang: str  # "es" or "en"
    crop_metadata: Optional[dict]  # The JSON calculated from your tools
    visual_description: Optional[str]
    correction_feedback: Optional[str]
