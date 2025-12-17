import os
import structlog
from dotenv import load_dotenv

logger = structlog.getLogger()

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    ve = ValueError("Warning: 'GEMINI_API_KEY' was not set correctly in '.env' file. Detected value: {GEMINI_API_KEY}")
    logger.warning(f"{ve}")
    logger.warning(f"Set a valid value to access AgrIA's Chat Assistant services!")


class Config:
    REFLECTANCE_SCALE = 400.0  # default

    @classmethod
    def set_reflectance_scale(cls, value: float):
        cls.REFLECTANCE_SCALE = value
        print("REFLECTANCE_SCALE", value)
