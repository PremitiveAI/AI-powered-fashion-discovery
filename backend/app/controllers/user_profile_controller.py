# app/controller/models_controller.py
import os
import shutil
import uuid
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.config.env import env
from app.models.user_profile_model import UserProfileTable

UPLOAD_USER = "models/user_photo"
os.makedirs(UPLOAD_USER, exist_ok=True)

# UPLOAD PHOTO

def upload_photo(db: Session, profile_id: int | None, file: UploadFile):

    # Validate file type (basic)
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files allowed")

    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = f"{UPLOAD_USER}/{unique_name}"

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # IF ID PROVIDED → UPDATE
    if profile_id:

        profile = db.query(UserProfileTable).filter(
            UserProfileTable.id == profile_id
        ).first()

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        # delete old file
        if profile.imageUrl and os.path.exists(profile.imageUrl):
            os.remove(profile.imageUrl)

        profile.imageUrl = file_path
        message = "User photo updated successfully"

    # IF NO ID → CREATE NEW
    else:
        profile = UserProfileTable(
            imageUrl=file_path,
            status=1
        )

        db.add(profile)
        message = "User photo created successfully"

    db.commit()
    db.refresh(profile)

    return {
        "message": message,
        "profile_id": profile.id,
        "image_url": f"{env('BASE_URL')}{file_path}"
    }

def get_last_updated_user_photo(db: Session):

    profile = (
        db.query(UserProfileTable)
        .order_by(UserProfileTable.updatedAt.desc())
        .first()
    )

    if not profile:
        raise HTTPException(status_code=404, detail="No users found")

    return {
        "id": profile.id,
        "image_url": f"{env('BASE_URL')}{profile.imageUrl}" if profile.imageUrl else None,
        "updated_at": profile.updatedAt
    }