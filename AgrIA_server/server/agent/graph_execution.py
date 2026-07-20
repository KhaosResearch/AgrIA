import structlog
import json

from langchain_core.messages import HumanMessage
from typing import Literal
from langgraph.graph import StateGraph, START, END


from ..config.constants import BASE_CONTEXT_PATH
from ..config.llm_client import client, LLM_MODEL_NAME
from ..models.state_models import AgrIAState
from .nodes.conversation_node import basic_chat_node
from .nodes.fallback_node import fallback_rejection_node
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
builder.add_node(
    "fallback_rejection",
    lambda state: fallback_rejection_node(state, client, model_name),
)
builder.add_node(
    "report_generator", lambda state: generate_report_node(state, client, model_name)
)
builder.add_node("validate_report", validate_report_node)  # Fast code checking node


# 3. Define the routing edge logic
def router_edge_adapter(
    state: AgrIAState,
) -> Literal["basic_chat", "fallback_rejection", "report_generator"]:
    """Adapts our existing router return string to LangGraph's strict Type typing."""
    return deterministic_router(state)


# 4. Wire up the graph flow topology
# Instead of hardcoding paths, we tell START to use our conditional router function
builder.add_conditional_edges(
    START,
    router_edge_adapter,
    {
        "basic_chat": "basic_chat",
        "fallback_rejection": "fallback_rejection",
        "report_generator": "report_generator",
    },
)

# Every worker node in this layout is a terminal leaf node for this turn, so they route to END
builder.add_edge("basic_chat", END)
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

if __name__ == "__main__":
    print("==================================================")
    print("        EXECUTING COMPILED LANGGRAPH MACHINE     ")
    print("==================================================")

    # Setup Test Inputs for Report Node
    json_filepath = BASE_CONTEXT_PATH / "files/26002A001000010000EQ_example_es.json"
    with open(json_filepath, "r", encoding="utf-8") as f:
        mock_crop_json = json.load(f)

    msg = "###DESCRIBE_SHORT_IMAGE### Generate analysis."
    msg = (
        "Qué es un ecorregimen? Cuántos hay. que importes tienen y cómo accedo a ellos?"
    )
    input_state: AgrIAState = {
        "messages": [HumanMessage(content=msg)],
        "lang": "es",
        "crop_metadata": mock_crop_json,
        "visual_description": "Parcela irregular con cultivo de secano y zonas verdes estructuradas.",
    }

    # Execute the state graph run
    # LangGraph completely manages state modification, routing, and termination internally
    final_output_state = agria_graph.invoke(input_state)

    logger.info("[LANGGRAPH RUN COMPLETE]")
    logger.info(f"Final Message in History:\n{final_output_state['messages'][-1]}")
    print("==================================================")
