import uvicorn
from server.config.env_config import API_HOST, API_PORT
from server import create_app

app = create_app()

if __name__ == "__main__":
    # Runs via ASGI server container natively
    uvicorn.run("run:app", host=API_HOST, port=int(API_PORT), reload=True)
