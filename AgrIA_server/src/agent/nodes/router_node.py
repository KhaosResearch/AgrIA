import json
import structlog

from typing import Literal
from langchain_core.messages import BaseMessage

from ...models.chat_models import LocalChat
from ...models.state_models import AgrIAState
from ...utils.chat_utils import get_recent_history
from ...utils.nodes_utils import load_prompt_asset

logger = structlog.get_logger(__name__)

VALID_INTENTS = Literal[
    "report_generator", "cap_query", "basic_chat", "fallback_rejection"
]


def deterministic_router(state: AgrIAState, client, model_name: str) -> VALID_INTENTS:
    """
    Hybrid Graph Router:
    1. Fast-Path: Checks for explicit system tags (zero latency).
    2. LLM Intent Classifier: Evaluates natural language phrasing via structured JSON.
    """
    messages = state.get("messages", [])
    if not messages:
        return "basic_chat"

    last_msg: BaseMessage = messages[-1]
    text_content = str(last_msg.content).strip()

    # Search for report generation flag
    if "###DESCRIBE_SHORT_IMAGE###" in text_content:
        logger.info("⚡ Router Fast-Path Triggered: report_generator")
        return "report_generator"

    # Fallback to LLM intent classifier
    try:
        system_instruction = load_prompt_asset("INTENT.md")

        classifier_chat = LocalChat(
            client=client,
            model_name=model_name,
            system_instruction=system_instruction,
            history_init=get_recent_history(state["messages"][:-1]),
            max_context_tokens=8000,
        )

        # Use last few messages for context
        recent_messages = state["messages"][-4:]
        formatted_dialogue = "\n".join(
            [f"{m.type}: {m.content}" for m in recent_messages]
        )
        user_prompt = f"Classify the intent of the last message in this dialogue. Use the chat history as context:\n<last_user_message>\n{formatted_dialogue}\n</last_user_message>"
        response_wrapper = classifier_chat.send_message(user_prompt)

        # Parse output payload
        response_text = response_wrapper.text.strip()

        # Clean potential markdown wrapping if returned by local LLM
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1].replace("json", "").strip()

        data = json.loads(response_text)
        detected_intent = data.get("intent", "basic_chat")
        confidence = data.get("confidence", 0.0)

        logger.info(
            f"🧠 LLM Router classified intent: '{detected_intent.upper()}' (Confidence: {confidence})"
        )

        if detected_intent in [
            "basic_chat",
            "cap_query",
            "ecoschemes_rates",
            "fallback_rejection",
            "report_generator",
        ]:
            return detected_intent

    except Exception as e:
        logger.warning(
            f"⚠️ LLM Classifier failed or timed out: {e}. Falling back to 'basic_chat'."
        )

    return "basic_chat"
