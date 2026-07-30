import os
from dotenv import load_dotenv

load_dotenv()

UI_PORT = os.getenv("UI_PORT", "4200")
UI_HOST = os.getenv("UI_HOST", "localhost")
UI_URL = os.getenv("UI_URL", f"http://{UI_HOST}:{UI_PORT}")

API_PORT = os.getenv("API_PORT", "5000")
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_URL = os.getenv("API_URL", f"http://{UI_HOST}:{UI_PORT}")
