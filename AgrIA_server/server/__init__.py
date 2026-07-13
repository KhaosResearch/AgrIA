from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .benchmark.sr.constants import BM_DATA_DIR, BM_RES_DIR
from .config.constants import TEMP_DIR
from .config.env_config import UI_URL
from .endpoints.chat import router as chat_router
from .endpoints.parcel_finder import router as parcel_finder_router
from .utils.parcel_finder_utils import reset_dir

def create_app(ui_url: str = UI_URL) -> FastAPI:
    app = FastAPI(title="AgrIA Server")

    # FastAPI standard CORS middleware configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[ui_url, "http://127.0.0.1:4200", "http://localhost:4200"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Reset temp and benchmark dirs
    reset_dir(TEMP_DIR)
    reset_dir(BM_DATA_DIR)
    reset_dir(BM_RES_DIR)

    # Register Routers (Equivalent to Blueprints)
    app.include_router(chat_router)
    app.include_router(parcel_finder_router)

    return app