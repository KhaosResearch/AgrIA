from langchain_core.messages import AIMessage

from ...benchmark.vlm.constants import OG_CLASSIFICATION_FILEPATH
from ...models.chat_models import LocalChat
from ...models.state_models import AgrIAState
from ...utils.nodes_utils import load_prompt_asset


def ecoschemes_rates_node(state: AgrIAState, client, model_name: str) -> dict:
    """
    LangGraph Node: Returns ecoschemes rates & prices data by injecting
    rate context into a dedicated execution window.
    """
    lang = state.get("lang", "es")
    messages = state.get("messages", [])
    user_query = str(messages[-1].content) if messages else ""

    # Retrieve ecoschemes classification information
    with open(OG_CLASSIFICATION_FILEPATH, "r") as f:
        retrieved_context = f.read()

    # Load System Instructions
    raw_instruction = load_prompt_asset("RATES.md")
    system_instruction = raw_instruction.replace(
        "{lang}", "Spanish" if lang == "es" else "English"
    )

    # Construct compact user payload
    user_payload = f"""
<retrieved_regulatory_context>
{retrieved_context}
</retrieved_regulatory_context>

<user_question>
{user_query}
</user_question>
"""

    # Execute scoped Chat Call
    chat = LocalChat(
        client=client,
        model_name=model_name,
        system_instruction=system_instruction,
        max_context_tokens=8000,
    )

    response_wrapper = chat.send_message(user_payload)

    return {"messages": state["messages"] + [AIMessage(content=response_wrapper.text)]}
