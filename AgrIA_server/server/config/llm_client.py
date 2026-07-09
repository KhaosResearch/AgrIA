from google import genai
from langchain_openai import ChatOpenAI
from .config import GEMINI_API_KEY, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME

# client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def init_client(
    base_url: str = LLM_BASE_URL,
    api_key: str = LLM_API_KEY,
    temperature: float = 0.1,
    max_retries: int = 2,
):
    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=LLM_MODEL_NAME,
        temperature=temperature,
        max_retries=max_retries,
    )


client = init_client()
