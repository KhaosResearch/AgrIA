import json

from langchain_core.messages import AIMessage

from ...benchmark.vlm.constants import OG_CLASSIFICATION_FILEPATH
from ...models.chat_models import LocalChat
from ...models.state_models import AgrIAState
from ...utils.chat_utils import get_recent_history
from ...utils.nodes_utils import load_prompt_asset, secondary_intent_block


def _load_rates_context(lang: str) -> str:
    """Load the eco-scheme rate table for the requested language only.

    The full asset contains both EN and ES blocks (~11 KB). Injecting only the
    relevant language halves the token cost and avoids the model mixing
    languages in the output.
    """
    with open(OG_CLASSIFICATION_FILEPATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    lang_key = "ES" if lang == "es" else "EN"
    entries = data.get(lang_key, [])
    return json.dumps(entries, ensure_ascii=False, indent=2)


def ecoschemes_rates_node(state: AgrIAState, client, model_name: str) -> dict:
    """
    LangGraph Node: Returns ecoschemes rates & prices data by injecting
    rate context into a dedicated execution window.
    """
    lang = state.get("lang", "es")
    messages = state.get("messages", [])
    user_query = str(messages[-1].content) if messages else ""

    # Retrieve ecoschemes classification information (language-filtered)
    retrieved_context = _load_rates_context(lang)

    # Load System Instructions
    raw_instruction = load_prompt_asset("RATES.md")
    system_instruction = raw_instruction.replace(
        "{lang}", "Spanish" if lang == "es" else "English"
    )
    system_instruction += secondary_intent_block(state)

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
        history_init=get_recent_history(state["messages"][:-1]),
        max_context_tokens=25000,
    )

    response_wrapper = chat.send_message(user_payload)

    return {"messages": [AIMessage(content=response_wrapper.text)]}
