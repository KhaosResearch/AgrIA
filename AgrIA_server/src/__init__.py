from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

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

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        errors = exc.errors()
        first_error = errors[0] if errors else {}
        loc = first_error.get("loc", [])
        field_name = loc[-1] if loc else ""

        # Match when 'userInput' form parameter is missing or invalid
        if field_name in ["userInput", "userMessage"]:
            return JSONResponse(
                status_code=400, content={"error": "No user input provided"}
            )

        if field_name == "imageDate" or field_name == "selectedDate":
            return JSONResponse(
                status_code=400, content={"error": "No image date provided"}
            )

        if field_name == "lat" or field_name == "lng":
            return JSONResponse(
                status_code=400, content={"error": "Invalid or missing coordinates"}
            )

        if field_name == "image":
            return JSONResponse(
                status_code=400, content={"error": "No image file provided"}
            )

        return JSONResponse(
            status_code=400,
            content={"error": first_error.get("msg", "Validation error")},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

    # Reset temp and benchmark dirs
    reset_dir(TEMP_DIR)
    reset_dir(BM_DATA_DIR)
    reset_dir(BM_RES_DIR)

    # Register Routers (Equivalent to Blueprints)
    app.include_router(chat_router)
    app.include_router(parcel_finder_router)

    return app
