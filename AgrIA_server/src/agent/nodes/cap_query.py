from langchain_core.messages import AIMessage

from ...utils.rag_utils import get_or_create_knowledge_base, query_knowledge_base
from ...models.chat_models import LocalChat
from ...models.state_models import AgrIAState
from ...utils.nodes_utils import load_prompt_asset


def cap_query_node(state: AgrIAState, client, model_name: str) -> dict:
    """
    LangGraph Node: Handles CAP ecoschemes queries by injecting
    full, cached regulatory context into a dedicated execution window.
    """
    lang = state.get("lang", "es")
    messages = state.get("messages", [])
    user_query = str(messages[-1].content) if messages else ""

    # 1. Access knowledge base
    collection = get_or_create_knowledge_base(reset_database=False)

    # 2. Retrieve top 3 relevant passages matching query (~1,000 - 1,500 tokens)
    retrieved_context = query_knowledge_base(collection, user_query, n_results=7)

    # 3. Load System Instructions
    raw_instruction = load_prompt_asset("CAP_QUERY.md", lang)
    system_instruction = raw_instruction.replace(
        "{lang}", "Spanish" if lang == "es" else "English"
    )

    # 4. Construct compact user payload
    user_payload = f"""
<retrieved_regulatory_context>
{retrieved_context}
</retrieved_regulatory_context>

<user_question>
{user_query}
</user_question>
"""

    # 5. Execute scoped Chat Call
    chat = LocalChat(
        client=client,
        model_name=model_name,
        system_instruction=system_instruction,
        max_context_tokens=8000,  # Highly conservative window—no more 32k bloat!
    )

    response_wrapper = chat.send_message(user_payload)

    return {"messages": state["messages"] + [AIMessage(content=response_wrapper.text)]}
