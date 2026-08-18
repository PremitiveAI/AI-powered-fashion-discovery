# app/controller/models_controller.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.config.env import env
from app.models.models_category_model import CategoryModelTable
from app.models.model_gallery import ModelGallery


def create_or_update_category(db: Session, data: dict):

    category_id = data.get("id")

    # ---------------- UPDATE ----------------
    if category_id:
        category = db.query(CategoryModelTable).filter(
            CategoryModelTable.id == category_id,
            CategoryModelTable.status == 1
        ).first()

        if not category:
            raise HTTPException(status_code=404, detail="Category not found or inactive")

        # Update fields manually
        category.name = data.get("name")
        category.description = data.get("description")
        category.type = data.get("type")
        category.gallery_id = data.get("gallery_id")
        category.gender = data.get("gender")

        db.commit()
        db.refresh(category)

        return {
            "message": "Category updated successfully",
            "id": category.id
        }

    # ---------------- CREATE ----------------
    required_fields = ["name", "gallery_id", "gender"]

    for field in required_fields:
        if not data.get(field):
            raise HTTPException(
                status_code=400,
                detail=f"{field} is required"
            )

    new_category = CategoryModelTable(
        name=data.get("name"),
        description=data.get("description"),
        type=data.get("type"),
        gallery_id=data.get("gallery_id"),
        gender=data.get("gender"),
        status=1
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return {
        "message": "Category created successfully",
        "id": new_category.id
    }


# FETCH BY GENDER WITH GALLERY IMAGE
def get_category_list(db: Session, gender: str):

    data = (
        db.query(CategoryModelTable, ModelGallery)
        .join(ModelGallery, CategoryModelTable.gallery_id == ModelGallery.id)
        .filter(CategoryModelTable.gender == gender)
        .filter(CategoryModelTable.status == 1)
        .filter(ModelGallery.status == 1)
        .all()
    )

    result = []

    for category, gallery in data:
        result.append({
            "id": category.id,
            "name": category.name,
            "type": category.type,
            "description": category.description,
            "gallery_id": category.gallery_id,
            "image_url": f"{env('BASE_URL')}{gallery.image_url}",
            "gender": category.gender
        })

    return result