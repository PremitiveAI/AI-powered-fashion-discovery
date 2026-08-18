import os
import shutil
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
import httpx

from app.models.model_analysis_model import ModelAnalysisTable
from app.services.model_analysis_service import generate_prompt_from_image, generate_image_with_gemini
from app.config.env import env
from app.models.profile_model import ProfileTable
import requests
import uuid

UPLOAD_FOLDER = "uploads/models"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GENERATED_FOLDER = "products/createdUser"
os.makedirs(GENERATED_FOLDER, exist_ok=True)


BASE_DIR = os.path.abspath(os.getcwd())
GEN_IMAGE_DIR = os.path.join(BASE_DIR, "uploads", "createdUser")

def upload_and_analyze_model(db: Session, file: UploadFile, user_url: str = None):

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image file")

    file_path = f"{UPLOAD_FOLDER}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Generate prompt from Gemini
    prompt_text = generate_prompt_from_image(file_path)

    base_url = env("BASE_URL")
    model_url = f"{base_url}uploads/models/{file.filename}"

    # Save in DB
    record = ModelAnalysisTable(
        model_name=file.filename,
        model_url=model_url,
        user_url=user_url,
        prompt=prompt_text
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "message": "Model analyzed successfully",
        "id": record.id,
        "model_url": model_url,
        "prompt": prompt_text
    }

def get_prompt_and_photo(db: Session, profile_id: int, model_id: int):

    # Fetch profile photo
    profile = (
        db.query(ProfileTable.photo)
        .filter(ProfileTable.id == profile_id)
        .first()
    )
    print(profile)

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Fetch prompt
    model = (
        db.query(ModelAnalysisTable.prompt)
        .filter(ModelAnalysisTable.id == model_id)
        .first()
    )
    print(model)

    if not model:
        raise HTTPException(status_code=404, detail="Model record not found")
    
    final_photo = f"{env('BASE_URL')}{profile[0]}"
    return {
        "prompt": model[0],
        "photo": final_photo
    }

async def generate_gemini_image(db: Session, profile_id: int, model_id: int):

    # Fetch profile photo
    profile = (
        db.query(ProfileTable.photo)
        .filter(ProfileTable.id == profile_id)
        .first()
    )

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Fetch prompt
    model = (
        db.query(ModelAnalysisTable.prompt)
        .filter(ModelAnalysisTable.id == model_id)
        .first()
    )

    if not model:
        raise HTTPException(status_code=404, detail="Model record not found")

    prompt = model[0]
    photo_url = f"{env('BASE_URL')}{profile[0]}"

    # Download user image
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(photo_url)
    if response.status_code != 200:
        raise HTTPException(400, "Failed to load user image")

    user_bytes = response.content

    # Generate image using Gemini
    generated_bytes = generate_image_with_gemini(
        user_bytes=user_bytes,
        prompt=prompt
    )

    # Ensure directory exists
    os.makedirs(GEN_IMAGE_DIR, exist_ok=True)

    # Save file
    file_name = f"{uuid.uuid4()}.png"
    output_path = os.path.join(GEN_IMAGE_DIR, file_name)

    with open(output_path, "wb") as f:
        f.write(generated_bytes)

    return {
        "status": "success",
        "image_url": f"{env('BASE_URL')}uploads/createdUser/{file_name}"
    }

