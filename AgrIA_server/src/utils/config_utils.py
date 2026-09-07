import shutil
import structlog
import yaml

from pathlib import Path

from ..config.constants import CUSTOM_SKILLS_DIR

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


def ensure_hermes_skill_registered(custom_skills_dir: str = str(CUSTOM_SKILLS_DIR)):
    """Add all custom skills to `hermes` config file (`~/.hermes/config.yaml`) if not already present."""
    config_path = Path.home() / ".hermes" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config = {}
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f) or {}

    skills_config = config.setdefault("skills", {})
    external_dirs = skills_config.setdefault("external_dirs", [])

    if custom_skills_dir not in external_dirs:
        external_dirs.append(custom_skills_dir)
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        print(f"Registered {custom_skills_dir} in ~/.hermes/config.yaml")


def sync_skill_to_hermes(source_skill_dir: str):
    """Copy and paste all custom skills from `source_skill_dir` directory to `~/.hermes/skills` directory."""
    target_dir = Path.home() / ".hermes" / "skills" / "satellite-image-analysis"
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_skill_dir, target_dir)
    print("Synced skill to ~/.hermes/skills/satellite-image-analysis")
