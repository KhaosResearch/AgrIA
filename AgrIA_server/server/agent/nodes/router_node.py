import json
import structlog

from typing import Literal
from langchain_core.messages import BaseMessage

from ...models.chat_models import LocalChat
from ...models.state_models import AgrIAState
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
        system_instruction = load_prompt_asset("", "INTENT.md")

        # Fast, short-lived session with strict context boundaries
        classifier_chat = LocalChat(
            client=client,
            model_name=model_name,
            system_instruction=system_instruction,
            max_context_tokens=3000,
        )

        response_wrapper = classifier_chat.send_message(
            f'Classify this user message: "{text_content}"'
        )

        # Parse output payload
        response_text = response_wrapper.text.strip()

        # Clean potential markdown wrapping if returned by local LLM
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1].replace("json", "").strip()

        data = json.loads(response_text)
        detected_intent = data.get("intent", "basic_chat")
        confidence = data.get("confidence", 0.0)

        logger.info(
            f"🧠 LLM Router classified intent: '{detected_intent}' (Confidence: {confidence})"
        )

        if detected_intent in [
            "report_generator",
            "cap_query",
            "basic_chat",
            "fallback_rejection",
        ]:
            return detected_intent

    except Exception as e:
        logger.warning(
            f"⚠️ LLM Classifier failed or timed out: {e}. Falling back to 'basic_chat'."
        )

    return "basic_chat"
