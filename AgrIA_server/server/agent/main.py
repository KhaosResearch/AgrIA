import json
import structlog

from dataclasses import dataclass
from typing import List
from langchain_core.messages import BaseMessage, HumanMessage


from ..config.config import LLM_MODEL_NAME
from ..config.llm_client import client
from .graph_base import deterministic_router
from .graph_base import basic_chat_node, fallback_rejection_node
from ..models.state_models import AgrIAState
from .nodes.report_node import generate_report_node

logger = structlog.get_logger(__file__)


def simulate_graph_run(
    initial_state: AgrIAState, client, model_name: str
) -> AgrIAState:
    logger.info(f"--- Starting AgrIA Graph Routing ---")
    logger.info(f"Active Language Context: {initial_state['lang']}")

    # 1. Evaluate the routing logic deterministically
    next_node = deterministic_router(initial_state)
    logger.info(f"Decision: Router directed transaction to -> [{next_node}]")

    # 2. Execute the corresponding isolated worker node
    if next_node == "basic_chat":
        updated_state = basic_chat_node(initial_state, client, model_name)
    elif next_node == "fallback_rejection":
        updated_state = fallback_rejection_node(initial_state, client, model_name)
    elif next_node == "report_generator":
        logger.info("Routing to report generator (Step 3)...")
        updated_state = generate_report_node(initial_state, client, model_name)

    logger.info(f"Transaction Complete. Tokens saved by bypassing monolithic loading.")
    return updated_state


if __name__ == "__main__":
    import json
    from langchain_core.messages import HumanMessage

    # 1. Configuration & Client Inits (adjust imports as needed for your setup)
    model_name = LLM_MODEL_NAME  # standard global config string
    # 'client' and 'LLM_MODEL_NAME' should be initialized/imported above this block

    print("==================================================")
    print("      RUNNING INTEGRATED AGRIA STATE GRAPH TEST   ")
    print("==================================================")

    # ----------------------------------------------------------------
    # TEST CASE A: Standard Domain Greeting (Routes to basic_chat)
    # ----------------------------------------------------------------
    logger.info("[TEST A] Initiating Greeting Session...")
    state_a: AgrIAState = {
        "messages": [HumanMessage(content="Hola buenas tardes")],
        "lang": "es",
        "crop_metadata": None,
        "visual_description": None,
    }
    result_a = simulate_graph_run(state_a, client, model_name)
    logger.info(f"-> Final Node Output: {result_a['messages'][-1]}\n")

    # ----------------------------------------------------------------
    # TEST CASE B: Out of Scope Prompt (Routes to fallback_rejection)
    # ----------------------------------------------------------------
    logger.info("[TEST B] Initiating Out-of-Scope Prompt...")
    state_b: AgrIAState = {
        "messages": [HumanMessage(content="¿Cuál es el sentido de la vida?")],
        "lang": "es",
        "crop_metadata": None,
        "visual_description": None,
    }
    result_b = simulate_graph_run(state_b, client, model_name)
    logger.info(f"-> Final Node Output: {result_b['messages'][-1]}\n")

    # ----------------------------------------------------------------
    # TEST CASE C: Core Analysis Trigger (Routes to report_generator)
    # ----------------------------------------------------------------
    logger.info("[TEST C] Initiating Report Generation Flow...")

    # Load your actual local example JSON data
    json_filepath = "/home/miguel/Dev/AgrIA/AgrIA_server/assets/LLM_assets/context/files/26002A001000010000EQ_example_es.json"
    try:
        with open(json_filepath, "r", encoding="utf-8") as f:
            mock_crop_json = json.load(f)
    except FileNotFoundError:
        # Fallback dictionary structure if running outside local path environment
        mock_crop_json = {
            "Report_Type": "EcoScheme_Payment_Estimate",
            "Total_Parcel_Area_ha": 45.7332,
            "Calculation_Context": {
                "Rate_Applied": "Peninsular_Rates_Used_For_Final_Summary_Total",
                "Source": "Provisional base rates for Eco-schemes, 2025 CAP Campaign",
            },
            "Estimated_Total_Payment": [
                {
                    "Ecoscheme_ID": "P1",
                    "Ecoscheme_Name": "Pastoreo y Biodiversidad",
                    "Ecoscheme_Subtype": "Pastos Mediterr\u00e1neos",
                    "Land_Use_Class_Eligible": "MT, PA, PR, PS (7.07 ha)",
                    "Total_Area_ha": 7.0703,
                    "Peninsular": {
                        "Applied_Base_Payment_EUR": 27.27,
                        "Total_Base_Payment_EUR": 192.81,
                        "Total_with_Pluriannuality_EUR": 192.81,
                        "Applicable": "Si (Tarifa Plana)",
                    },
                    "Insular": {
                        "Applied_Base_Payment_EUR": 49.27,
                        "Total_Base_Payment_EUR": 348.35,
                        "Total_with_Pluriannuality_EUR": 348.35,
                        "Applicable": "Si (Tarifa Plana)",
                    },
                },
                {
                    "Ecoscheme_ID": "P3/P4",
                    "Ecoscheme_Name": "Rotaci\u00f3n y Siembra Directa",
                    "Ecoscheme_Subtype": "Regad\u00edo",
                    "Land_Use_Class_Eligible": "TA (22.75 ha)",
                    "Total_Area_ha": 22.7474,
                    "Peninsular": {
                        "Applied_Base_Payment_EUR": 141.742439,
                        "Total_Base_Payment_EUR": 3224.27,
                        "Total_with_Pluriannuality_EUR": 3792.95,
                        "Applicable": "Si (Tramo 1 aplicado)",
                    },
                    "Insular": {
                        "Applied_Base_Payment_EUR": 221.742439,
                        "Total_Base_Payment_EUR": 5044.06,
                        "Total_with_Pluriannuality_EUR": 5612.74,
                        "Applicable": "Si (Tramo 1 aplicado)",
                    },
                },
                {
                    "Ecoscheme_ID": "P5 (B)",
                    "Ecoscheme_Name": "Espacios de Biodiversidad",
                    "Ecoscheme_Subtype": "Bajo Agua",
                    "Land_Use_Class_Eligible": "AG (0.41 ha)",
                    "Total_Area_ha": 0.4099,
                    "Peninsular": {
                        "Applied_Base_Payment_EUR": 145.098595,
                        "Total_Base_Payment_EUR": 59.48,
                        "Total_with_Pluriannuality_EUR": 59.48,
                        "Applicable": "Si (Tarifa Plana)",
                    },
                    "Insular": {
                        "Applied_Base_Payment_EUR": 0.0,
                        "Total_Base_Payment_EUR": 0.0,
                        "Total_with_Pluriannuality_EUR": 0.0,
                        "Applicable": "Si (Tarifa Plana)",
                    },
                },
                {
                    "Ecoscheme_ID": "P6/P7",
                    "Ecoscheme_Name": "Cubiertas Vegetales o Espont\u00e1neas",
                    "Ecoscheme_Subtype": "Terreno Llano",
                    "Land_Use_Class_Eligible": "FY, VI (9.49 ha)",
                    "Total_Area_ha": 9.4863,
                    "Peninsular": {
                        "Applied_Base_Payment_EUR": 59.12,
                        "Total_Base_Payment_EUR": 560.83,
                        "Total_with_Pluriannuality_EUR": 797.98,
                        "Applicable": "Si (Tramo 1 aplicado)",
                    },
                    "Insular": {
                        "Applied_Base_Payment_EUR": 99.12,
                        "Total_Base_Payment_EUR": 940.28,
                        "Total_with_Pluriannuality_EUR": 1177.44,
                        "Applicable": "Si (Tramo 1 aplicado)",
                    },
                },
                {
                    "Ecoscheme_ID": "N/A",
                    "Ecoscheme_Name": "Non-Eligible",
                    "Ecoscheme_Subtype": None,
                    "Land_Use_Class_Eligible": "CA, ED, FO, IM, ZU",
                    "Total_Area_ha": 6.0193,
                    "Peninsular": {
                        "Applied_Base_Payment_EUR": "N/A",
                        "Total_Base_Payment_EUR": "N/A",
                        "Total_with_Pluriannuality_EUR": "N/A",
                        "Applicable": "N/A",
                    },
                    "Insular": {
                        "Applied_Base_Payment_EUR": "N/A",
                        "Total_Base_Payment_EUR": "N/A",
                        "Total_with_Pluriannuality_EUR": "N/A",
                        "Applicable": "N/A",
                    },
                },
            ],
            "Final_Results": {
                "Applicable_Ecoschemes": ["P1", "P3/P4", "P5 (B)", "P6/P7"],
                "Total_Aid_without_Pluriannuality_EUR": 4037.39,
                "Total_Aid_with_Pluriannuality_EUR": 4885.52,
            },
        }

    state_c: AgrIAState = {
        # The key trigger phrase that the router intercepts
        "messages": [
            HumanMessage(
                content="###DESCRIBE_SHORT_IMAGE### Please review this parcel data."
            )
        ],
        "lang": "es",
        "crop_metadata": mock_crop_json,
        "visual_description": (
            "Esta imagen satélite muestra una parcela irregular delimitada y dividida por líneas blancas. "
            "Destacan extensas zonas doradas de cultivo seco, combinadas con cuadrículas de vegetación verde "
            "y algunas edificaciones en el centro. Al sur se observan masas forestales oscuras."
        ),
    }

    result_c = simulate_graph_run(state_c, client, model_name)
    logger.info(f"-> Final Node Output:\n{result_c['messages'][-1]}\n")

    print("==================================================")
    print("                ALL GRAPH TESTS COMPLETE          ")
    print("==================================================")
