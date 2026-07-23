import json
import structlog

from typing import Optional
from fastapi import APIRouter, Form, UploadFile, File, HTTPException

from src.config.chat_config import CHAT as chat
from src.services.chat_service import (
    generate_user_response,
    get_parcel_description,
    get_role_and_content,
    get_suggestion_for_chat,
)

logger = structlog.get_logger()
router = APIRouter()


@router.get("/hello-world")
def hello_world():
    return {"response": "Hello, World!"}


@router.post("/send-user-input")
def send_user_input(
    userMessage: str = Form(...),
    image: UploadFile | str | None = File(None),
    isDetailedDescription: str = Form("false"),
    lang: str = Form("en"),
):
    try:
        is_detailed_description = "true" in isDetailedDescription.lower()

        if image is not None and not isinstance(image, str):
            file, filename = image.file, image.filename
        else:
            file, filename = None, None
        if userMessage is not None and len(userMessage) > 0:
            response_text = generate_user_response(
                userMessage, is_detailed_description, lang, file, filename
            )
            return {"response": response_text}
        else:
            msg = "No user input provided"
            ve = ValueError(msg)
            logger.error(str(ve))
            raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load-parcel-data-to-chat")
def send_parcel_info_to_chat(
    imageDate: str = Form(...),
    landUses: str = Form(...),
    query: str = Form(...),
    imageFilename: Optional[str] = Form(None),
    isDetailedDescription: str = Form("false"),
    lang: str = Form("es"),
):
    try:
        image_date = imageDate.split("/")[-1]
        parsed_land_uses = json.loads(landUses)
        parsed_query = json.loads(query)
        is_detailed_description = "true" in isDetailedDescription.lower()

        response = get_parcel_description(
            image_date,
            parsed_land_uses,
            parsed_query,
            imageFilename,
            is_detailed_description,
            lang,
        )
        return {"response": response}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error loading parcel to chat:\n")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-input-suggestion")
def get_input_suggestion(lang: str = Form("es")):
    try:
        chat_history = chat.get_history()
        if not chat_history:
            raise ValueError("No valid history provided.")
        response = get_suggestion_for_chat(chat_history, lang)
        return {"response": response}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error getting suggestion:\n")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/load-active-chat-history")
def load_active_chat_history():
    try:
        chat_history = chat.get_history()
        if not chat_history:
            raise ValueError("No valid history provided.")
        response = get_role_and_content(chat_history)
        return {"response": response}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Error getting history:\n")
        raise HTTPException(status_code=500, detail=str(e))
