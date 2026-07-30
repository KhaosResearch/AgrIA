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
    1. Fast-Path: Checks for explicit system tags or empty input (zero latency).
    2. LLM Intent Classifier: Evaluates natural language phrasing via structured JSON.
    """
    messages = state.get("messages", [])
    if not messages:
        return "basic_chat"

    last_msg: BaseMessage = messages[-1]
    text_content = str(last_msg.content).strip()

    # Fast-Path 1: Empty input check
    if not text_content:
        return "basic_chat"

    # Fast-Path 2: System tag check for report generation
    if "###DESCRIBE_SHORT_IMAGE###" in text_content:
        logger.info("⚡ Router Fast-Path Triggered: report_generator")
        return "report_generator"

    # Fallback: LLM Intent Classifier
    try:
        # Load system instruction as transient SystemMessage
        system_instruction = load_prompt_asset("INTENT.md")

        classifier_chat = LocalChat(
            client=client,
            model_name=model_name,
            system_instruction=system_instruction,
            history_init=get_recent_history(messages[:-1], max_turns=4),
            max_context_tokens=8000,
        )

        user_prompt = (
            f"Classify the intent of the last message in this context:\n"
            f"<last_user_message>\n{text_content}\n</last_user_message>"
        )

        response_wrapper = classifier_chat.send_message(user_prompt)
        response_text = response_wrapper.text.strip()

        if response_text.startswith("```"):
            response_text = response_text.split("```")[1].replace("json", "").strip()

        data = json.loads(response_text)
        detected_intent = data.get("intent", "basic_chat")
        confidence = data.get("confidence", 0.0)

        logger.info(
            f"🧠 LLM Router classified intent: '{detected_intent.upper()}' (Confidence: {confidence})"
        )

        valid_intents = {
            "basic_chat",
            "cap_query",
            "ecoschemes_rates",
            "fallback_rejection",
            "report_generator",
        }

        if detected_intent in valid_intents:
            return detected_intent

    except Exception as e:
        logger.warning(
            f"⚠️ LLM Classifier failed or timed out: {e}. Falling back to 'basic_chat'."
        )

    return "basic_chat"
