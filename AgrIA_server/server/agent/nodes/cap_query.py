from langchain_core.messages import AIMessage
from ...models.chat_models import LocalChat
from ...models.state_models import AgrIAState
from ...utils.nodes_utils import load_prompt_asset
from ...utils.pdf_loader import load_cached_regulatory_context


def cap_query_node(state: AgrIAState, client, model_name: str) -> dict:
    """
    LangGraph Node: Handles CAP/PAC ecorregímenes queries by injecting
    full, cached regulatory context into a dedicated execution window.
    """
    lang = state.get("lang", "es")
    messages = state.get("messages", [])
    user_query = str(messages[-1].content) if messages else ""

    # 1. Load System Prompt Instructions
    raw_instruction = load_prompt_asset(lang, "cap_expert.md")
    system_instruction = raw_instruction.replace(
        "{lang}", "Spanish" if lang == "es" else "English"
    )

    # 2. Fetch Cached Regulatory Context (JIT)
    regulatory_context = load_cached_regulatory_context()

    # 3. Assemble Scoped User Payload
    user_payload = f"""
<regulatory_context>
{regulatory_context}
</regulatory_context>

<user_question>
{user_query}
</user_question>
"""

    # 4. Instantiate Scoped LocalChat Instance
    chat = LocalChat(
        client=client,
        model_name=model_name,
        system_instruction=system_instruction,
        max_context_tokens=32000,  # Expand window size for full document context
    )

    response_wrapper = chat.send_message(user_payload)

    # 5. Return updated state to LangGraph
    return {"messages": state["messages"] + [AIMessage(content=response_wrapper.text)]}
