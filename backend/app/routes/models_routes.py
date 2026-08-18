# app/routes/models_routes.py
from fastapi import APIRouter, Depends, UploadFile, File, Form,Request,Body,HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.docs.swagger_headers import SwaggerAPIHeaders
from typing import List
from app.schemas.model_gallery_schema import ModelGalleryCreate, ModelGalleryResponse
from app.controllers.user_profile_controller import upload_photo,get_last_updated_user_photo
from app.controllers.model_gallery_controller import upload_gallery_image,fetch_gallery, delete_gallery
from app.controllers.models_category_controller import create_or_update_category,get_category_list
from app.controllers.models_controller import save_models_controller,generate_gemini_image,get_models_with_details_controller

models_router = APIRouter(
    prefix="/models",
    dependencies=[Depends(SwaggerAPIHeaders)]
)

@models_router.post("/user-photo", tags=["Models"])
def save_user_photo(
    profile_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return upload_photo(db, profile_id, file)

@models_router.get("/last-user-photo", tags=["Models"])
def get_last_user_photo(db: Session = Depends(get_db)):
    return get_last_updated_user_photo(db)

# 1️⃣ Upload (POST)
@models_router.post("/upload-gallery", tags=["Models"])
def upload_gallery(
    type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return upload_gallery_image(db, file, type)


# 2️⃣ Fetch (POST with type in form or query)
@models_router.post("/gallery-list", tags=["Models"])
def gallery_list(
    type: str = Form(...),
    db: Session = Depends(get_db)
):
    return fetch_gallery(db, type)


# 3️⃣ Soft delete (POST with id in form)
@models_router.post("/gallery-delete",  tags=["Models"])
def gallery_delete(
    id: int = Form(...),
    db: Session = Depends(get_db)
):
    return delete_gallery(db, id)

@models_router.post("/category_create", tags=["Models"])
def create_or_update(
    body: dict = Body(
        ...,
        example={
            "id": 1,                 # optional (only for update)
            "name": "Minimal",
            "description": "Quiet Luxury",
            "type": "category",
            "gallery_id": 4,
            "gender": "male"
        }
    ),
    db: Session = Depends(get_db)
):
    return create_or_update_category(db, body)

@models_router.post("/category-list", tags=["Models"])
def category_list(
    body: dict = Body(
        ...,
        example={
            "gender": "male"
        }
    ),
    db: Session = Depends(get_db)
):
    gender = body.get("gender")

    if not gender:
        return {"error": "gender is required"}

    return get_category_list(db, gender)

@models_router.post("/save-models",tags=["Models"])
async def save_models(
    file: UploadFile = File(...),
    category_id: int = Form(...),  # This is BODY, not header
    db: Session = Depends(get_db)
):
    return await save_models_controller(file, category_id, db)

@models_router.post("/user-try-on",tags=["Models"])
async def generate_try_on(
    user_id: int = Body(...),
    model_id: int = Body(...),
    db: Session = Depends(get_db)
):
    return await generate_gemini_image(
        db=db,
        user_id=user_id,
        model_id=model_id
    )

@models_router.post("/models-list", tags=["Models"])
async def get_models_with_details(
    gender: str = Body(...),
    category_ids: List[int] = Body(...),  # required
    db: Session = Depends(get_db)
):
    if not category_ids:
        raise HTTPException(status_code=400, detail="At least one category_id is required")

    return await get_models_with_details_controller(
        db=db,
        gender=gender,
        category_ids=category_ids
    )