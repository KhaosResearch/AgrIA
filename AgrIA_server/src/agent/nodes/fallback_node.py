import structlog

from ...models.state_models import AgrIAState
from ...utils.nodes_utils import execute_scoped_chat

logger = structlog.get_logger(__file__)


def fallback_rejection_node(state: AgrIAState, client, model_name: str) -> dict:
    return execute_scoped_chat(state, client, model_name, "FALLBACK.md", False)
