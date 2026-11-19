import structlog

from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from ..config.llm_client import client, LLM_MODEL_NAME
from ..models.state_models import AgrIAState, INTENT_REGISTRY
from .nodes.cap_query_node import cap_query_node
from .nodes.cap_interruption_node import cap_interruption_node
from .nodes.basic_chat_node import basic_chat_node
from .nodes.app_usage_node import app_usage_node
from .nodes.fallback_node import fallback_rejection_node
from .nodes.ecoscheme_rates_node import ecoschemes_rates_node
from .nodes.report_node import generate_report_node
from .nodes.router_node import (
    cap_guard_edge,
    deterministic_router,
    clear_cap_workflow,
    _clarification_message,
)
from .nodes.validation_node import validate_report_node, evaluation_router_edge
from .nodes.cap_document_inspector_node import cap_document_inspector_node
from .nodes.cap_slot_guard_node import cap_slot_guard_node
from .nodes.cap_application_node import cap_application_node

logger = structlog.get_logger(__file__)


def inspector_edge(state: AgrIAState) -> str:
    """Route a document inspection result.

    The inspector only ever produces evidence in `cap_alignment`, which
    `cap_application_node` is the sole consumer of, so its result always goes
    there: routing to the advisory query would drop the extracted slots.
    """
    return "cap_application" if state.get("cap_alignment") else "cap_query"


# Define graph routing logic
def route_adapter(state: AgrIAState, model_name: str = LLM_MODEL_NAME) -> str:
    """Adapter function to pass model execution runtime args to the router."""
    return deterministic_router(state, client=client, model_name=model_name)


def clarify_node(state: AgrIAState) -> dict:
    """Terminal node reached when the router is unsure of the intent.

    The classifier returned a label it did not trust (below the confidence
    threshold), so instead of guessing we ask one short clarifying question.
    This is deterministic (no LLM call) and keeps the CAP workflow untouched.
    """
    lang = state.get("lang", "es")
    return {
        "messages": [AIMessage(content=_clarification_message(lang))],
        "secondary_intent": None,
    }


# The router may send the graph to any registered intent plus the clarify node.
# Deriving the map from INTENT_REGISTRY keeps it in sync with the classifier by
# construction: a new intent added to the registry is routable immediately.
ROUTER_TARGETS = {intent: intent for intent in INTENT_REGISTRY}
ROUTER_TARGETS["clarify"] = "clarify"


def build_graph() -> StateGraph[AgrIAState]:
    # Initialize the Graph Builder using our State structural definition
    builder = StateGraph(AgrIAState)
    model_name = LLM_MODEL_NAME

    # We use simple lambda wrappers to pass your custom client runtime arguments
    builder.add_node(
        "basic_chat", lambda state: basic_chat_node(state, client, model_name)
    )
    builder.add_node(
        "app_usage", lambda state: app_usage_node(state, client, model_name)
    )
    builder.add_node(
        "cap_query", lambda state: cap_query_node(state, client, model_name)
    )
    builder.add_node(
        "fallback_rejection",
        lambda state: fallback_rejection_node(state, client, model_name),
    )
    builder.add_node(
        "ecoschemes_rates",
        lambda state: ecoschemes_rates_node(state, client, model_name),
    )
    builder.add_node(
        "report_generator",
        lambda state: generate_report_node(state, client, model_name),
    )
    builder.add_node("validate_report", validate_report_node)  # Fast code checking node

    # CAP clarification chain: document / guard -> application -> advisory
    builder.add_node(
        "cap_document_inspector",
        lambda state: cap_document_inspector_node(state, client, model_name),
    )
    builder.add_node(
        "cap_slot_guard",
        lambda state: cap_slot_guard_node(state, client, model_name),
    )
    builder.add_node(
        "cap_application",
        lambda state: cap_application_node(state, client, model_name),
    )
    builder.add_node(
        "cap_interruption",
        lambda state: cap_interruption_node(state, client, model_name),
    )
    builder.add_node("clear_cap_workflow", clear_cap_workflow)
    builder.add_node("clarify", clarify_node)

    # Wire up the graph flow topology. The target map is derived from the intent
    # registry (plus the clarify node), so it cannot drift from the classifier.
    builder.add_conditional_edges(START, route_adapter, ROUTER_TARGETS)

    # Add terminal nodes
    builder.add_edge("basic_chat", END)
    builder.add_edge("app_usage", END)
    builder.add_edge("cap_query", END)
    builder.add_edge("ecoschemes_rates", END)
    builder.add_edge("fallback_rejection", END)
    builder.add_edge("clarify", END)

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

    # CAP clarification: both entry points feed the application node, which
    # merges slots, validates and decides between the next question and the
    # advisory answer. `pending_action` alone drives resumability.
    builder.add_conditional_edges(
        "cap_document_inspector",
        inspector_edge,
        {
            "cap_application": "cap_application",
            "cap_query": "cap_query",
        },
    )
    builder.add_conditional_edges(
        "cap_slot_guard",
        cap_guard_edge,
        {
            "cap_interruption": "cap_interruption",
            "cap_application": "cap_application",
        },
    )

    builder.add_edge("cap_interruption", END)
    builder.add_edge("cap_application", END)
    builder.add_edge("clear_cap_workflow", END)

    return builder


# Compile the State Machine
builder = build_graph()
checkpointer = MemorySaver()
AGRIA_GRAPH = builder.compile(checkpointer=checkpointer)
