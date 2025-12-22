from server import create_app
from server.config.env_config import API_HOST, API_PORT

app = create_app()

if __name__ == '__main__':
    app.run(host=API_HOST, port=API_PORT, debug=True)
