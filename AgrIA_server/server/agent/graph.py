import structlog
import json

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END


from ..config.constants import BASE_PROMPTS_PATH
from ..config.llm_client import client, LLM_MODEL_NAME
from ..models.state_models import AgrIAState
from .nodes.cap_query import cap_query_node
from .nodes.conversation_node import basic_chat_node
from .nodes.fallback_node import fallback_rejection_node
from .nodes.ecoscheme_rates_node import ecoschemes_rates_node
from .nodes.report_node import generate_report_node
from .nodes.router_node import deterministic_router
from .nodes.validation_node import validate_report_node, evaluation_router_edge

logger = structlog.get_logger(__file__)

# 1. Initialize the Graph Builder using our State structural definition
builder = StateGraph(AgrIAState)
model_name = LLM_MODEL_NAME

# 2. Register our worker nodes
# We use simple lambda wrappers to pass your custom client runtime arguments
builder.add_node("basic_chat", lambda state: basic_chat_node(state, client, model_name))
builder.add_node("cap_query", lambda state: cap_query_node(state, client, model_name))
builder.add_node(
    "fallback_rejection",
    lambda state: fallback_rejection_node(state, client, model_name),
)
builder.add_node(
    "ecoschemes_rates", lambda state: ecoschemes_rates_node(state, client, model_name)
)
builder.add_node(
    "report_generator", lambda state: generate_report_node(state, client, model_name)
)
builder.add_node("validate_report", validate_report_node)  # Fast code checking node


# 3. Define the routing edge logic
def route_adapter(state: AgrIAState) -> str:
    """Adapter function to pass model execution runtime args to the router."""
    return deterministic_router(state, client=client, model_name=model_name)


# 4. Wire up the graph flow topology
# Instead of hardcoding paths, we tell START to use our conditional router function
builder.add_conditional_edges(
    START,
    route_adapter,
    {
        "basic_chat": "basic_chat",
        "cap_query": "cap_query",
        "ecoschemes_rates": "ecoschemes_rates",
        "fallback_rejection": "fallback_rejection",
        "report_generator": "report_generator",
    },
)

# Every worker node in this layout is a terminal leaf node for this turn, so they route to END
builder.add_edge("basic_chat", END)
builder.add_edge("cap_query", END)
builder.add_edge("ecoschemes_rates", END)
builder.add_edge("fallback_rejection", END)
builder.add_edge("report_generator", "validate_report")

# The Dynamic Self-Correction Feedback Edge!
builder.add_conditional_edges(
    "validate_report",
    evaluation_router_edge,
    {
        "report_generator": "report_generator",  # Loops back to fix mistakes
        "__end__": END,  # Exits to user if perfect
    },
)
# 5. Compile the State Machine
agria_graph = builder.compile()

