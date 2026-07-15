import pathlib
import structlog

logger = structlog.get_logger(__file__)


def upload_context_document(context_file_path: str) -> str | None:
    """Reads a local context document and returns its text content for local context injection.

    Replaces legacy cloud upload behavior.
    """
    path = pathlib.Path(context_file_path)
    if path.exists() and path.is_file():
        try:
            # Handle standard text extensions
            if path.suffix.lower() in [".txt", ".md", ".json", ".csv"]:
                return path.read_text(encoding="utf-8")

            # Simple placeholder text fallback for non-text files
            return f"[Local File Reference: {path.name}]"
        except Exception as e:
            logger.error(f"Error reading local document context: {e}")
            return None
    return None
