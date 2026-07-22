import structlog
import json

from langchain_core.messages import AIMessage, HumanMessage
from typing import Literal
from langgraph.graph import StateGraph, START, END

from ..config.constants import BASE_CONTEXT_PATH
from ..config.llm_client import client, LLM_MODEL_NAME
from ..models.state_models import AgrIAState
from .nodes.cap_query import cap_query_node
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
builder.add_node("cap_query", lambda state: cap_query_node(state, client, model_name))
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
        "cap_query": "cap_query",
    },
)

# Every worker node in this layout is a terminal leaf node for this turn, so they route to END
builder.add_edge("basic_chat", END)
builder.add_edge("fallback_rejection", END)
builder.add_edge("report_generator", "validate_report")
builder.add_edge("cap_query", END)

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
    # 1. Models & Config initialization

    print("==================================================")
    print("      RUNNING INTEGRATED AGRIA STATE GRAPH TEST   ")
    print("==================================================")

    # ----------------------------------------------------------------
    # TEST CASE A: Greeting (basic_chat)
    # ----------------------------------------------------------------
    logger.info("[TEST A] Initiating Greeting Session...")
    state_a: AgrIAState = {
        "messages": [HumanMessage(content="Hola buenas tardes")],
        "lang": "es",
        "crop_metadata": None,
        "visual_description": None,
        "correction_feedback": None,
    }
    result_a = agria_graph.invoke(state_a)
    logger.info(f"-> Node Input: {state_a['messages'][-1]}")
    logger.info(f"-> Node Output: {result_a['messages'][-1]}\n")

    # ----------------------------------------------------------------
    # TEST CASE B: Out of Scope (fallback_rejection)
    # ----------------------------------------------------------------
    logger.info("[TEST B] Initiating Out-of-Scope Prompt...")
    state_b: AgrIAState = {
        "messages": [HumanMessage(content="¿Cuál es el sentido de la vida?")],
        "lang": "es",
        "crop_metadata": None,
        "visual_description": None,
        "correction_feedback": None,
    }
    result_b = agria_graph.invoke(state_b)
    logger.info(f"-> Node Input: {state_b['messages'][-1]}")
    logger.info(f"-> Node Output: {result_b['messages'][-1]}\n")

    # ----------------------------------------------------------------
    # TEST CASE C: Report Flow (report_generator + validation loop)
    # ----------------------------------------------------------------
    logger.info("[TEST C] Initiating Report Generation Flow...")
    json_filepath = BASE_CONTEXT_PATH / "files/26002A001000010000EQ_example_es.json"
    with open(json_filepath, "r", encoding="utf-8") as f:
        mock_crop_json = json.load(f)

    state_c: AgrIAState = {
        "messages": [
            HumanMessage(content="###DESCRIBE_SHORT_IMAGE### Genera el informe.")
        ],
        "lang": "es",
        "crop_metadata": mock_crop_json,
        "visual_description": "Parcela irregular con cultivo de secano y zonas verdes.",
        "correction_feedback": None,
    }
    result_c = agria_graph.invoke(state_c)
    logger.info(f"-> Final Report Input: {state_c['messages'][-1]}")
    logger.info(f"-> Final Report Output:\n{result_c['messages'][-1]}\n")

    # ----------------------------------------------------------------
    # TEST CASE D: CAP / Regulatory Query (cap_query_node + pypdf JIT)
    # ----------------------------------------------------------------
    logger.info("[TEST D] Initiating Ecorregímenes Query Flow...")
    state_d: AgrIAState = {
        "messages": [
            HumanMessage(
                content="¿Cuáles son los requisitos para cobrar el ecorregimen de cubiertas vegetales en cultivos leñosos P7 y cómo afectan las cuestas en el terreno? Cita tus fuentes: los nombres de los documentos o fuentes que uses."
            )
        ],
        "lang": "es",
        "crop_metadata": None,
        "visual_description": None,
        "correction_feedback": None,
    }

    result_d = agria_graph.invoke(state_d)
    logger.info(f"-> Regulatory Answer Input: {state_d['messages'][-1]}")
    logger.info(f"-> Regulatory Answer Output:\n{result_d['messages'][-1]}\n")

    print("==================================================")
    print("                ALL GRAPH TESTS COMPLETE          ")
    print("==================================================")
