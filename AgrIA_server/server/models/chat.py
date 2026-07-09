import base64
from pathlib import Path
from PIL import Image
import io
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


class LocalChat:

    def __init__(self, client, model_name: str, system_instruction: str, history_init=None):
        self.client = client
        self.model_name = model_name
        self.history = InMemoryChatMessageHistory()

        # Initialize base state
        self.history.add_message(SystemMessage(content=system_instruction))
        if history_init:
            # If set_initial_history() returns standard LangChain messages, add them here
            self.history.add_messages(history_init)

    def get_history(self):
        """Replicates the history tracking endpoint expected by chat.py."""
        # Returns the underlying list of LangChain messages
        return self.history.messages

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
                encoded_image = base64.b64encode(path.read_bytes()).decode(
                    "utf-8"
                )
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

    def send_message(self, content_input):
        # Format human message content based on input structure
        if isinstance(content_input, list):
            formatted_content = [
                self._process_input_item(item) for item in content_input
            ]
        else:
            formatted_content = [self._process_input_item(content_input)]

        # Append human message to the ongoing state history
        user_msg = HumanMessage(content=formatted_content)
        self.history.add_message(user_msg)

        # Get all compiled messages up to this point
        all_messages = self.history.messages

        # Execute API call to local LLM backend
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
