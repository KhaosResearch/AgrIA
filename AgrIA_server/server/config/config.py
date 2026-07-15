import os
import structlog

from dotenv import load_dotenv
from .constants import SEN2SR_SR_DIR

os.environ["SEN2SR_OUTPUT_DIR"] = str(
    SEN2SR_SR_DIR
)  # Set ENV VAR for sen2sr_tools package

logger = structlog.getLogger()

load_dotenv()

# LLM CREDENTIALS & MODEL
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", None)
LLM_API_KEY = os.environ.get("LLM_API_KEY", None)
LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", None)

# AUX VLM CREDENTIALS & MODEL
VLM_BASE_URL = os.environ.get("VLM_BASE_URL", None)
VLM_API_KEY = os.environ.get("VLM_API_KEY", None)
VLM_MODEL_NAME = os.environ.get("VLM_MODEL_NAME", None)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)

if GEMINI_API_KEY in ["", None]:
    ve = ValueError(
        "Warning: 'GEMINI_API_KEY' was not set correctly in '.env' file. Detected value: {GEMINI_API_KEY}"
    )
    logger.warning(f"{ve}")
    logger.warning("Set a valid value to access AgrIA's Chat Assistant services!")


class Config:
    REFLECTANCE_SCALE = 400.0  # default

    @classmethod
    def set_reflectance_scale(cls, value: float):
        cls.REFLECTANCE_SCALE = value
        logger.debug(f"REFLECTANCE_SCALE {value}")
