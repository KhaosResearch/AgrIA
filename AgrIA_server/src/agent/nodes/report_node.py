import json
import structlog

from langchain_core.messages import AIMessage

from ...config.constants import BASE_PROMPTS_PATH
from ...models.chat_models import LocalChat
from ...models.state_models import AgrIAState
from ...utils.chat_utils import get_recent_history

logger = structlog.get_logger(__file__)


def load_prompt_template(lang: str, filename: str) -> str:
    """Loads prompt files from our prompts-as-code folder."""
    file_path = BASE_PROMPTS_PATH / lang / filename
    return file_path.read_text(encoding="utf-8")


def generate_report_node(state: AgrIAState, client, model_name: str) -> dict:
    """
    LangGraph Node: Isolates context windows to generate a structured
    Markdown agricultural analysis report safely within token limits.
    """
    lang = state.get("lang", "es")
    metadata = state.get("crop_metadata", {})
    history_messages = state["messages"]

    # Align state key naming uniform checks
    visual_desc = (
        state.get("visual_description")
        or state.get("visual_desc")
        or "No image data provided."
    )

    # 1. Fetch our optimized base prompt template
    raw_instruction = load_prompt_template(lang, "REPORT.md")

    # Dynamic runtime string injection for localization constraints
    system_instruction = raw_instruction.replace(
        "{lang}", "Spanish" if lang == "es" else "English"
    )

    # Check state feedback
    feedback = state.get("correction_feedback")
    feedback_block = ""

    if feedback and feedback != "PASSED":
        feedback_block = f"""
<critical_retry_warning>
ATTENTION: Your previous output failed verification checks. You MUST fix these errors in this attempt:
{feedback}
</critical_retry_warning>
"""
        history_messages = history_messages[:-1]  # Removed failed report

    # 2. Package data inside XML (feedback included)
    user_content = f"""{feedback_block}
Please compile the agricultural report matching the template constraints using these source materials.

<visual_description>
{visual_desc}
</visual_description>

<parcel_metadata_json>
{json.dumps(metadata, ensure_ascii=False, indent=2)}
</parcel_metadata_json>
"""

    chat = LocalChat(
        client=client,
        model_name=model_name,
        system_instruction=system_instruction,
        history_init=get_recent_history(history_messages),
        max_context_tokens=10000,
    )

    # Send payload through your standard class invocation pipeline
    response_wrapper = chat.send_message(user_content)

    # Return updates back cleanly to the graph lifecycle state machine
    return {
        "messages": [AIMessage(content=response_wrapper.text)],
        "correction_feedback": None,  # Reset feedback after every attempt
    }

if __name__ == "__main__":
    # Concrete test execution framework
    mock_state: AgrIAState = {
        "messages": [],
        "lang": "es",
        "crop_metadata": None,
        "visual_description": None,
    }

    json_filepath = BASE_PROMPTS_PATH / "examples/26002A001000010000EQ_example_es.json"
    with open(json_filepath, "r", encoding="utf-8") as f:
        mock_state["crop_metadata"] = json.load(f)

    # Populating uniform visual data tags
    mock_state["visual_description"] = (
        "Esta imagen satélite muestra una parcela irregular delimitada y dividida por líneas blancas. "
        "Destacan extensas zonas doradas de cultivo seco, combinadas con cuadrículas de vegetación verde."
    )

    node_update = generate_report_node(mock_state)
    print(
        "\n[Node Finished Operation Success] Output Payload:\n",
        node_update["messages"][-1],
    )
