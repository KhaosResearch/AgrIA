from dotenv import load_dotenv

from .env_config import GEMINI_API_KEY

load_dotenv()

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env")

class Config:
    REFLECTANCE_SCALE = 400.0  # default

    @classmethod
    def set_reflectance_scale(cls, value: float):
        cls.REFLECTANCE_SCALE = value
        print("REFLECTANCE_SCALE", value)

