from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
import os
import uuid

from app.services.photo_service import generate_final_image_bytes, gemini_has_face, gemini_is_safe_tryon
from app.docs.swagger_headers import SwaggerAPIHeaders
from app.config.env import env

photo_router = APIRouter(
    prefix="/photo",
    tags=["photos"],
    dependencies=[Depends(SwaggerAPIHeaders)]
)

# ✅ ABSOLUTE PROJECT ROOT
BASE_DIR = os.path.abspath(os.getcwd())

# ✅ STORAGE PATHS
CLOTH_STORAGE_DIR = os.path.join(BASE_DIR, "storage")
TRY_ON_DIR = os.path.join(BASE_DIR, "try_on")


@photo_router.post("/try-on")
async def try_on(
    user_photo: UploadFile = File(...),
    cloth_url: str = Form(...)
):
    def extract_cloth_id(value: str) -> str:
        if value.startswith("http"):
            if "/storage/" not in value:
                raise HTTPException(400, "Invalid cloth image URL")
            return value.split("/storage/", 1)[-1]
        return value

    cloth_url = extract_cloth_id(cloth_url)

    if not user_photo.content_type.startswith("image/"):
        raise HTTPException(400, "user_photo must be an image")

    cloth_path = os.path.normpath(
        os.path.join(CLOTH_STORAGE_DIR, cloth_url)
    )

    if not cloth_path.startswith(CLOTH_STORAGE_DIR):
        raise HTTPException(400, "Invalid cloth path")

    if not os.path.exists(cloth_path):
        raise HTTPException(404, f"Cloth image not found: {cloth_path}")

    with open(cloth_path, "rb") as f:
        cloth_bytes = f.read()

    user_bytes = await user_photo.read()
    if not user_bytes:
        raise HTTPException(400, "Invalid user image")

    if not gemini_has_face(user_bytes):
        return {
            "status": "Fail",
            "message": "No human face detected"
        }
    
    if not gemini_is_safe_tryon(user_bytes):
        return {
            "status": "Fail",
            "message": "Invalid image: nudity or unsafe content detected"
        }

    os.makedirs(TRY_ON_DIR, exist_ok=True)

    output_name = f"{uuid.uuid4()}.png"
    output_path = os.path.join(TRY_ON_DIR, output_name)

    generate_final_image_bytes(
        user_bytes=user_bytes,
        cloth_bytes=cloth_bytes,
        output_path=output_path
    )

    return {
        "status": "success",
        "image_url": f"{env('BASE_URL')}try_on/{output_name}"
    }


def extract_cloth_id(value: str) -> str:
    # If full URL, extract path
    if value.startswith("http"):
        path = value.split("/storage/", 1)[-1]
        return path

    return value