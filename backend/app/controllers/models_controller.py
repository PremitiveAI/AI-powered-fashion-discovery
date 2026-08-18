import os
from fastapi import HTTPException,UploadFile
from sqlalchemy.orm import Session
import uuid
import httpx
from typing import List
from sqlalchemy.orm import joinedload
from sqlalchemy import func

from app.models.tbl_models import ModelTable, ModelTypeTable, ModelTryOnTable
from app.models.user_profile_model import UserProfileTable
from app.services.model_analysis_service import generate_prompt_from_image,generate_image_with_gemini
from app.services.decision_models_engine import analyze_image
from app.services.product_service import ProductService
from app.config.env import env

UPLOAD_FOLDER = "uploads/models"
base_url = env("BASE_URL")

async def save_models_controller(file,category_id: int, db: Session):
    # 1️⃣ Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid image file")

    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="Empty file")

    # 2️⃣ Save image locally
    file_extension = os.path.splitext(file.filename)[1] 
    if not file_extension:
        raise HTTPException(status_code=400, detail="File extension missing")
    
    random_filename = f"{uuid.uuid4().hex}{file_extension}"

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(UPLOAD_FOLDER, random_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(contents)


    model_url = f"uploads/models/{random_filename}"

    # 3️⃣ Generate prompt
    prompt_text = generate_prompt_from_image(file_path)

    # 4️⃣ Run AI analyze
    analysis_result = await analyze_image(contents)

    gender_detected = None
    try:
        gender_detected = analysis_result["data"][0]["items"][0].get("gender")
    except Exception:
        pass

    try:
        # 5️⃣ Save main model
        new_model = ModelTable(
            model_name=file.filename,
            modle_url=model_url,
            prompt=prompt_text,
            gender=gender_detected,
            category_id=category_id,
            status=True
        )

        db.add(new_model)
        db.flush()

        inserted_types = []

        # 6️⃣ Save type records
        for person in analysis_result.get("data", []):
            for item in person.get("items", []):
                model_type = ModelTypeTable(
                    models_id=new_model.id,
                    category=item.get("category"),
                    type=item.get("type"),
                    subtype=item.get("subtype"),
                    color=item.get("color"),
                    pattern=item.get("pattern"),
                    brand=item.get("brand"),
                    gender = item.get("gender"),
                    status=True
                )

                db.add(model_type)
                db.flush()
                inserted_types.append(model_type)

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    # 7️⃣ Prepare response
    final_url = f"{base_url}{new_model.modle_url}"
    return {
        "message": "Model saved and analyzed successfully",
        "model": {
            "id": new_model.id,
            "model_name": new_model.model_name,
            "model_url": final_url,
            "prompt": new_model.prompt,
            "gender": new_model.gender,
            "status": new_model.status,
            "createdAt": new_model.createdAt,
            "updatedAt": new_model.updatedAt
        },
        "items": [
            {
                "id": t.id,
                "category": t.category,
                "type": t.type,
                "subtype": t.subtype,
                "color": t.color,
                "pattern": t.pattern,
                "brand": t.brand,
                "gender": t.gender,
                "status": t.status,
                "createdAt": t.createdAt,
                "updatedAt": t.updatedAt,
            }
            for t in inserted_types
        ]
    }

async def generate_gemini_image(
    db: Session,
    user_id: int,
    model_id: int
):
    # 1️⃣ Fetch user profile
    profile = (
        db.query(UserProfileTable)
        .filter(UserProfileTable.id == user_id)
        .first()
    )

    if not profile or not profile.imageUrl:
        raise HTTPException(status_code=404, detail="User profile not found")

    # 2️⃣ Fetch model
    model = (
        db.query(ModelTable)
        .filter(ModelTable.id == model_id)
        .first()
    )

    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    photo_url = f"{base_url}{profile.imageUrl}"
    prompt = model.prompt

    # 3️⃣ Download user image
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(photo_url)

    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to load user image")

    user_bytes = response.content

    # 4️⃣ Generate Gemini image
    generated_bytes = generate_image_with_gemini(
        user_bytes=user_bytes,
        prompt=prompt
    )

    # 5️⃣ Save generated image
    GEN_IMAGE_DIR = "uploads/createdUser"
    os.makedirs(GEN_IMAGE_DIR, exist_ok=True)

    file_name = f"{uuid.uuid4().hex}.png"
    output_path = os.path.join(GEN_IMAGE_DIR, file_name)

    with open(output_path, "wb") as f:
        f.write(generated_bytes)

    relative_path = f"uploads/createdUser/{file_name}"

    # 6️⃣ Save into tbl_models_try_on
    try_on_record = ModelTryOnTable(
        models_id=model_id,
        user_url=relative_path,
        status=True
    )

    db.add(try_on_record)
    db.commit()
    db.refresh(try_on_record)

    final_url = f"{base_url}{relative_path}"
    return {
        "status": "success",
        "user_id": user_id,
        "model_id": model_id,
        "try_on_id": try_on_record.id,
        "image_url": final_url
    }

async def get_models_with_details_controller1(
    db: Session,
    gender: str,
    category_ids: List[int]
):

    if gender.lower() not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Invalid gender value")

    models = (
        db.query(ModelTable)
        .options(joinedload(ModelTable.category))
        .filter(
            func.lower(ModelTable.gender) == gender.lower(),
            ModelTable.category_id.in_(category_ids)
        )
        .all()
    )

    if not models:
        raise HTTPException(status_code=404, detail="No models found")

    response_data = []

    for model in models:

        # Latest try_on
        latest_try_on = (
            db.query(ModelTryOnTable)
            .filter(ModelTryOnTable.models_id == model.id)
            .order_by(ModelTryOnTable.updatedAt.desc())
            .first()
        )

        latest_user_url = (
            f"{base_url}{latest_try_on.user_url}"
            if latest_try_on else None
        )

        # Types
        types = (
            db.query(ModelTypeTable)
            .filter(ModelTypeTable.models_id == model.id)
            .all()
        )

        items = [
            {
                "id": t.id,
                "category": t.category,
                "type": t.type,
                "subtype": t.subtype,
                "color": t.color,
                "pattern": t.pattern,
                "brand": t.brand,
                "gender": t.gender,
                "status": t.status,
            }
            for t in types
        ]

        response_data.append({
            "id": model.id,
            "model_name": model.model_name,
            "model_url": f"{base_url}{model.modle_url}",
            "user_url": latest_user_url,
            "prompt": model.prompt,
            "gender": model.gender,
            "status": model.status,
            "category": {
                "id": model.category.id if model.category else None,
                "name": model.category.name if model.category else None,
                "type": model.category.type if model.category else None,
                "description": model.category.description if model.category else None,
                "gender": model.category.gender if model.category else None,
            },
            "items": items
        })

    return {
        "status": "success",
        "data": response_data
    }



async def get_models_with_details_controller(
    db: Session,
    gender: str,
    category_ids: List[int]
):
    if gender.lower() not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Invalid gender value")

    models = (
        db.query(ModelTable)
        .options(joinedload(ModelTable.category))
        .filter(
            func.lower(ModelTable.gender) == gender.lower(),
            ModelTable.category_id.in_(category_ids)
        )
        .all()
    )

    if not models:
        raise HTTPException(status_code=404, detail="No models found")

    response_data = []

    for model in models:

        latest_try_on = (
            db.query(ModelTryOnTable)
            .filter(ModelTryOnTable.models_id == model.id)
            .order_by(ModelTryOnTable.updatedAt.desc())
            .first()
        )

        latest_user_url = (
            f"{base_url}{latest_try_on.user_url}"
            if latest_try_on else None
        )

        types = (
            db.query(ModelTypeTable)
            .filter(ModelTypeTable.models_id == model.id)
            .all()
        )

        raw_items = [
            {
                "id": t.id,
                "category": t.category,
                "type": t.type,
                "subtype": t.subtype,
                "color": t.color,
                "pattern": t.pattern,
                "brand": t.brand,
                "gender": t.gender,
                "status": t.status,
                "shade": None
            }
            for t in types
        ]

        enriched_items = ProductService.search_products_for_items(raw_items)

        response_data.append({
            "id": model.id,
            "model_name": model.model_name,
            "model_url": f"{base_url}{model.modle_url}",
            "user_url": latest_user_url,
            "prompt": model.prompt,
            "gender": model.gender,
            "status": model.status,
            "category": {
                "id": model.category.id if model.category else None,
                "name": model.category.name if model.category else None,
                "type": model.category.type if model.category else None,
                "description": model.category.description if model.category else None,
                "gender": model.category.gender if model.category else None,
            },
            "items": enriched_items
        })

    return {
        "status": "success",
        "data": response_data
    }


