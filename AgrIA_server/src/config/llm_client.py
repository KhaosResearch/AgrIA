import structlog
from google import genai
from langchain_openai import ChatOpenAI
from .config import (
    GEMINI_API_KEY,
    IS_VLM_TEXT_ONLY,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL_NAME,
    VLM_API_KEY,
    VLM_BASE_URL,
    VLM_MODEL_NAME,
)

logger = structlog.get_logger(__file__)


def init_client(
    base_url: str = LLM_BASE_URL,
    api_key: str = LLM_API_KEY,
    model: str = LLM_MODEL_NAME,
    temperature: float = 0.4,
    max_retries: int = 2,
):
    # Guard clause: If key or config is missing/empty, do not initialize
    if not api_key or not base_url:
        logger.warning(
            "Skipping ChatOpenAI initialization: base_url or api_key is missing."
        )
        return None

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_retries=max_retries,
    )


client = init_client(temperature=0.6)
vlm_client = None
if GEMINI_API_KEY not in [None, ""]:
    vlm_client = genai.Client(api_key=GEMINI_API_KEY)
elif all(v not in (None, "") for v in (VLM_BASE_URL, VLM_API_KEY, VLM_MODEL_NAME)):
    if not IS_VLM_TEXT_ONLY:
        vlm_client = init_client(VLM_BASE_URL, VLM_API_KEY, VLM_MODEL_NAME)
    else:
        from run_agent import AIAgent

        vlm_client = AIAgent(
            model=VLM_MODEL_NAME,
            base_url=VLM_BASE_URL,
            api_key=VLM_API_KEY,
            ephemeral_system_prompt="You are a direct geospatial data summarizer. Translate satellite metrics into a natural language description. Output ONLY the description text (50-60 words). Absolute silence on everything else: no greetings, no markdown bold headers, no bullet points, no word count stats, and no post-response justification.",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
        )
