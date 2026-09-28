from fastapi import APIRouter
from run_agent import AIAgent
from structlog import get_logger

from ..config.constants import BASE_PROMPTS_PATH
from ..config.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME

router = APIRouter()
logger = get_logger(__name__)

with open(BASE_PROMPTS_PATH / "ROLE.md", "r", encoding="utf-8") as f:
    sys_prompt = f.read()

hermes_agent = AIAgent(
    model=LLM_MODEL_NAME,
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
    ephemeral_system_prompt=sys_prompt,
    quiet_mode=True,
    skip_context_files=True,
    skip_memory=True,
)

conversations: dict[
    str, list
] = {}  # Helps keep several conversations in memory (TESTING ONLY)


@router.post("/chat")
async def chat(message: str):
    # retrieve current agent context and add additional data to it
    # context = hermes_agent._get_tool_call_id_static("context")
    # context.add_document(open(BASE_PROMPTS_PATH / "ROLE.md").read())
    # context.add_path(BASE_PROMPTS_PATH / "APP_USAGE.md")
    # context.add_url("https://www.fega.gob.es/es/pepac-2023-2027/ayudas-directas/ecorregimenes")

    response = hermes_agent.chat(message)

    return {"response": response}


# ---

# ---


@router.post("/conversation")
async def conversation(conversation_id: str, message: str):
    history = conversations.setdefault(conversation_id, [])
    response = hermes_agent.run_conversation(message, conversation_history=history)
    history.extend(response["messages"])
    return {"response": response["final_response"]}
