import json
import structlog

from typing import Optional
from fastapi import APIRouter, Form, UploadFile, File, HTTPException

from server.services.chat_service import *

logger = structlog.get_logger()
router = APIRouter()


@router.get("/hello-world")
def hello_world():
    return {"response": "Hello, World!"}


@router.post("/send-user-input")
def send_user_input(userInput: str = Form(...)):
    try:
        response_text = generate_user_response(userInput)
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-image")
def send_image(
    image: UploadFile = File(...),
    isDetailedDescription: str = Form("false"),
    lang: str = Form("en"),
):
    try:
        is_detailed_description = "true" in isDetailedDescription.lower()
        response_text = get_image_description(
            image.file, image.filename, lang, is_detailed_description
        )
        return {"response": response_text}
    except Exception as e:
        logger.exception("Error sending image:\n")
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
