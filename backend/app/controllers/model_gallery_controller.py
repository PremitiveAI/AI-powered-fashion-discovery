import os
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from app.models.model_gallery import ModelGallery, GalleryType
from app.config.env import env


UPLOAD_DIR = "models/gallery"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


# Upload image
def upload_gallery_image(db: Session, file: UploadFile, type: str):
    if type not in ["models", "category"]:
        raise HTTPException(status_code=400, detail="Invalid type")

    file_extension = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    image_url = f"{UPLOAD_DIR}/{unique_name}"

    new_data = ModelGallery(
        image_url=image_url,
        type=type,
        status=1
    )

    db.add(new_data)
    db.commit()
    db.refresh(new_data)


    return {
        "id": new_data.id,
        "image_url":  f"{env('BASE_URL')}{new_data.image_url}",
        "type": new_data.type,
        "status": new_data.status
    }


# Fetch by type and status=1
def fetch_gallery(db: Session, type: str):
    if type not in ["models", "category"]:
        raise HTTPException(status_code=400, detail="Invalid type")

    data = (
        db.query(ModelGallery)
        .filter(ModelGallery.type == type)
        .filter(ModelGallery.status == 1)
        .all()
    )

    return [
        {
            "id": item.id,
            "image_url": f"{env('BASE_URL')}{item.image_url}",
            "type": item.type,
            "status": item.status
        }
        for item in data
    ]


# Soft delete (status=0)
def delete_gallery(db: Session, id: int):
    data = (
        db.query(ModelGallery)
        .filter(ModelGallery.id == id)
        .filter(ModelGallery.status == 1)
        .first()
    )

    if not data:
        raise HTTPException(status_code=404, detail="Data not found")

    data.status = 0
    db.commit()

    return {"message": "Deleted successfully"}