import os
import structlog

from inspect import isawaitable
from datetime import datetime
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import FileResponse
from typing import Optional

from ..config.constants import TEMP_DIR
from ..utils.parcel_finder_utils import (
    check_cadastral_data,
    is_coord_in_zones,
    reset_dir,
)
from ..services.parcel_finder_service import get_parcel_image

logger = structlog.get_logger(__file__)

router = APIRouter()


async def _await_if_needed(result):
    if isawaitable(result):
        return await result
    return result


@router.post("/load-parcel-description")
async def load_parcel_description(lang: str = Form("es")):
    try:
        parcel_desc_file = os.path.join(TEMP_DIR, f"parcel_desc-{lang}.txt")
        content = "..."

        if os.path.exists(parcel_desc_file):
            with open(parcel_desc_file, "r", encoding="utf-8") as file:
                content = file.read()
        return {"response": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/find-parcel")
async def find_parcel(
    selectedDate: str = Form(...),
    isFromCadastralReference: str = Form("False"),
    cadastralReference: Optional[str] = Form(None),
    parcelGeometry: Optional[str] = Form("None"),
    parcelMetadata: Optional[str] = Form(None),
    coordinates: Optional[str] = Form(None),
    province: Optional[str] = Form(None),
    municipality: Optional[str] = Form(None),
    polygon: Optional[str] = Form(None),
    parcelId: Optional[str] = Form(None),
):
    reset_dir(TEMP_DIR, [".png"])
    init = datetime.now()
    try:
        is_from_cadastral_reference = "True" in isFromCadastralReference
        actual_geometry = None if parcelGeometry == "None" else parcelGeometry

        actual_coords = None
        if coordinates and coordinates != "None":
            actual_coords = list(map(float, coordinates.split(",")))

        actual_cad_ref = cadastralReference
        if is_from_cadastral_reference:
            actual_cad_ref = check_cadastral_data(
                cadastralReference, province, municipality, polygon, parcelId
            )

        geometry, metadata, url_image_address = await _await_if_needed(
            get_parcel_image(
                actual_cad_ref,
                selectedDate,
                is_from_cadastral_reference,
                actual_geometry,
                parcelMetadata,
                actual_coords,
            )
        )

        logger.info(f"\nTOTAL TIME TAKEN: {datetime.now() - init}\n")
        return {
            "response": {
                "cadastralReference": actual_cad_ref,
                "geometry": geometry,
                "imagePath": url_image_address,
                "metadata": metadata,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/is-coord-in-zone")
async def is_coord_in_zone(lat: float = Form(...), lng: float = Form(...)):
    try:
        return {"response": is_coord_in_zones(lng, lat)}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or missing coordinates")


# FastAPI handles serving directory static media assets safely using FileResponse
@router.get("/uploads/{filename}")
async def uploaded_file(filename: str):
    file_path = os.path.join(os.getcwd(), TEMP_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
