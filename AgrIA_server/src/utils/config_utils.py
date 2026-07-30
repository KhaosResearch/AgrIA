import structlog

logger = structlog.get_logger(__file__)


def load_system_instructions(filepath):
    """
    Reads AgrIA's system instructions from a text file
    Arguments:
        filepath (str): Path to the text file.
    Returns:
        content (str): File content. Empty str ("") if file not found.
    """
    try:
        with open(filepath, "r") as f:
            content = f.read().strip()
    except FileNotFoundError:
        logger.error(f"Error: System instruction file not found at {filepath}")
        content = ""
    finally:
        return content
