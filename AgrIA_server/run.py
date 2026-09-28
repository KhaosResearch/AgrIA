import uvicorn
from src import create_app
from src.config.env_config import API_HOST, API_PORT
from src.utils.config_utils import ensure_hermes_skill_registered

ensure_hermes_skill_registered()
app = create_app()

if __name__ == "__main__":
    # Runs via ASGI server container natively
    uvicorn.run("run:app", host=API_HOST, port=int(API_PORT), reload=True)
