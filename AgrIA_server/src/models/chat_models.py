import asyncio
import base64
import inspect
import io
import openai
import structlog

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pathlib import Path
from PIL import Image

logger = structlog.get_logger(__file__)


class LocalChat:
    def __init__(
        self,
        client,
        model_name: str,
        system_instruction: str,
        history_init=None,
        max_context_tokens: int = 30000,
    ):
        self.client = client
        self.model_name = model_name
        self.history = InMemoryChatMessageHistory()
        self.max_context_tokens = max_context_tokens

        # Initialize base state
        self.history.add_message(SystemMessage(content=system_instruction))
        if history_init:
            # If set_initial_history() returns standard LangChain messages, add them here
            self.history.add_messages(history_init)

    def get_history(self):
        """Replicates the history tracking endpoint expected by chat.py."""
        # Returns the underlying list of LangChain messages
        return self.history.messages

    def _count_tokens(self, messages: list[BaseMessage]) -> int:
        """
        Crude local token estimation.
        For precise production matching, use `tiktoken` or `transformers.AutoTokenizer`.
        """
        total_tokens = 0
        for msg in messages:
            if isinstance(msg.content, str):
                total_tokens += (
                    len(msg.content) // 4
                )  # Rough heuristic: 4 chars ~ 1 token
            elif isinstance(msg.content, list):
                for item in msg.content:
                    if item.get("type") == "text":
                        total_tokens += len(item.get("text", "")) // 4
                    elif item.get("type") == "image_url":
                        total_tokens += 1000  # High safety fallback for vision items
        return total_tokens

    def _summarize_old_history(self, messages_to_summarize: list[BaseMessage]) -> str:
        """Invokes the client to compress older conversation history."""
        if not messages_to_summarize:
            return ""

        # Format history into text for the summarizer
        formatted_history = []
        for m in messages_to_summarize:
            role = "User" if isinstance(m, HumanMessage) else "Assistant"
            content = (
                m.content if isinstance(m.content, str) else "[Multimodal Content]"
            )
            formatted_history.append(f"{role}: {content}")

        history_text = "\n".join(formatted_history)

        system_prompt = "You are an expert chat summarizer. Retain crucial operational constraints, context, decisions, and facts."
        instruction = (
            "Summarize this historical chat segment efficiently in 150-250 words:"
        )

        msg = [
            ("system", system_prompt),
            ("human", f"{instruction}\n\n{history_text}"),
        ]
        try:
            # Re-using the client to summarize
            summary_method = getattr(self.client, "ainvoke", None)
            if summary_method is not None:
                summary_response = asyncio.run(summary_method(msg))
            else:
                summary_response = self.client.invoke(msg)
            return summary_response.content
        except Exception as e:
            logger.error(f"Failed to auto-summarize history: {e}")
            return "System Note: Earlier history truncated due to context limit constraints."

    def enforce_context_limits(self, user_msg: HumanMessage):
        """Checks total token pressure and compresses older history if limits are breached."""
        all_messages = self.history.messages
        all_tokens = self._count_tokens(all_messages) + self._count_tokens([user_msg])

        logger.debug(f"Counted Tokens: {all_tokens}")
        logger.debug(
            f"{all_tokens} > {self.max_context_tokens}? {all_tokens > self.max_context_tokens}"
        )

        # If safely under budget, change nothing
        if all_tokens <= self.max_context_tokens:
            return

        self.summarize_history()

    def summarize_history(self):
        logger.info(
            f"Context length exceeded threshold {self.max_context_tokens} max)! Managing history memory..."
        )

        all_messages = self.history.messages

        # Keep System Prompt (index 0) and the last 6 messages intact (approx 3 user-assistant turns)
        system_message = all_messages[0]
        recent_messages = all_messages[-6:]
        middle_messages = all_messages[1:-6]

        if not middle_messages:
            # If we are overflowing on just the last 6 messages, we must truncate older items aggressively
            recent_messages = all_messages[-4:]
            middle_messages = all_messages[1:-4]

        # Summarize the middle segment
        summary_text = self._summarize_old_history(middle_messages)

        # Build memory injection block
        memory_message = SystemMessage(
            content=f"--- CONTEXT SUMMARY OF OLDER CONVERSATION ---\n{summary_text}\n--------------------------------------------"
        )

        # Re-build memory with: [System Message] -> [Context Summary] -> [Recent Context turns]
        new_messages = [system_message, memory_message] + recent_messages

        # Clear and swap internal storage
        self.history.clear()
        self.history.add_messages(new_messages)

        logger.debug(f"New history entries: {len(self.history.messages)}")

    def _process_input_item(self, item):
        """Converts local inputs (strings, files, or PIL Images) into OpenAI-compatible structures."""
        # 1. Handle Text
        if isinstance(item, str):
            return {"type": "text", "text": item}

        # 2. Handle PIL Images or File paths
        if isinstance(item, Image.Image) or str(type(item)).lower() in [
            "imagefile",
            "pngimagefile",
        ]:
            buffered = io.BytesIO()
            # Default to PNG for safety, or JPEG if your pipeline prefers it
            item.save(buffered, format="PNG")
            img_bytes = buffered.getvalue()
            encoded_image = base64.b64encode(img_bytes).decode("utf-8")
            return {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{encoded_image}"},
            }

        # 3. Handle a string path if an image file path is passed
        if isinstance(item, (str, Path)) and Path(item).exists():
            path = Path(item)
            if path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
                encoded_image = base64.b64encode(path.read_bytes()).decode("utf-8")
                mime = (
                    f"image/{path.suffix.lower().replace('.', '')}"
                    if path.suffix.lower() != ".jpg"
                    else "image/jpeg"
                )
                return {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{encoded_image}"},
                }

        # Fallback if unknown
        return {"type": "text", "text": str(item)}

    def send_message(self, content_input: str, retry_send: bool = True):
        # Format human message content based on input structure
        if isinstance(content_input, list):
            formatted_content = [
                self._process_input_item(item) for item in content_input
            ]
        else:
            formatted_content = [self._process_input_item(content_input)]

        # Append human message to the ongoing state history
        user_msg = HumanMessage(content=formatted_content)

        self.enforce_context_limits(user_msg)

        try:
            self.history.add_message(user_msg)

            # Get all compiled messages up to this point
            all_messages = self.history.messages

            # Execute API call to local LLM backend
            invoke_method = getattr(self.client, "ainvoke", None)
            if invoke_method is not None:
                response = asyncio.run(invoke_method(all_messages))
            else:
                response = self.client.invoke(all_messages)

            # Append model response back into memory tracking
            self.history.add_message(AIMessage(content=response.content))

            # Replicate the `.text` attribute behavior to prevent code breaking downstream
            class ResponseWrapper:
                def __init__(self, text):
                    self.text = text

                def __str__(self):
                    return self.text

            return ResponseWrapper(response.content)
        except openai.BadRequestError as e:
            msg = str(e).lower()

            is_context_overflow = any(
                s in msg
                for s in (
                    "length of the input prompt",
                    "maximum input length",
                    "maximum context length",
                    "context length",
                    "context window",
                    "input_tokens",
                )
            )
            if retry_send and is_context_overflow in str(e):
                self.summarize_history()
                return self.send_message(content_input, False)

            raise e
