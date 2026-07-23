import structlog

from langgraph.graph import StateGraph, START, END


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

# Define graph routing logic
def route_adapter(state: AgrIAState, model_name: str = LLM_MODEL_NAME) -> str:
    """Adapter function to pass model execution runtime args to the router."""
    return deterministic_router(state, client=client, model_name=model_name)

def build_graph() -> StateGraph[AgrIAState]:
    # Initialize the Graph Builder using our State structural definition
    builder = StateGraph(AgrIAState)
    model_name = LLM_MODEL_NAME

    # Register our worker nodes
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

    # Wire up the graph flow topology
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

    # Add terminal nodes
    builder.add_edge("basic_chat", END)
    builder.add_edge("cap_query", END)
    builder.add_edge("ecoschemes_rates", END)
    builder.add_edge("fallback_rejection", END)

    # Add non-terminal and conditional nodes
    builder.add_edge("report_generator", "validate_report")
    builder.add_conditional_edges(
        "validate_report",
        evaluation_router_edge,
        {
            "report_generator": "report_generator",  # Loops back to fix mistakes
            "__end__": END,  # Exits to user if perfect
        },
    )

# Compile the State Machine
builder = build_graph()
AGRIA_GRAPH = builder.compile()
