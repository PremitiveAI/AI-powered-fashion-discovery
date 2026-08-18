
from fastapi import UploadFile 
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime
from app.models.admin_gallery_model import AdminGallery
from app.config.env import env
import json, re, math, os


# ============================================================
# FILE UTILITIES
# ============================================================
def secure_filename(name: str):
    return re.sub(r"[^A-Za-z0-9._-]", "_", Path(name).name)

# def save_local_file(user_id: str,  file: UploadFile):
#     folder = Path(f"storage/{user_id}")
#     folder.mkdir(parents=True, exist_ok=True)
#     path = folder / secure_filename(file.filename)
#     with open(path, "wb") as f:
#         f.write(file.file.read())
#     return str(path).replace("\\", "/")

async def save_local_file(user_id: str,  file: UploadFile):
    contents = await file.read()
    return save_local_file2(user_id, file.filename, contents, True)



def save_local_file2(admin_id: int, filename: str, contents: bytes, gallery: False) -> str:
    # Ensure admin-specific folder exists
    folder = env("STORAGE_DIR")
    folder = os.path.join(folder, str(admin_id))
    os.makedirs(folder, exist_ok=True)

    # Extract extension from original filename
    _, ext = os.path.splitext(filename)


    # Build new filename with timestamp + extension
    file_name_prifix = "product_search_"
    if gallery:
        file_name_prifix = ""

    file_name = f"{file_name_prifix}{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
    file_path = os.path.join(folder, file_name)

    # Save file
    with open(file_path, "wb") as f:
        f.write(contents)

    return str(file_path).replace("\\", "/")



def save_image(db: Session, details: dict):
    obj = AdminGallery(**details)
    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj

async def process_single_file(db: Session, userId: str, file: UploadFile):
    saved_path = await save_local_file(userId, file)
    print("saved_path ======================>", saved_path)
    # Calculate file size in MB 
    file.file.seek(0, os.SEEK_END) # move to end of file 
    size_bytes = file.file.tell() # get position = size in bytes 
    file.file.seek(0) # reset pointer

    values = {
        "imagePath": saved_path.replace("\\", "/"),
        "title": file.filename, # use filename as title 
        "type": "image", # or derive from your business logic 
        "mimeType": file.content_type, # FastAPI UploadFile has content_type 
        "fileSizeMB": round(size_bytes / (1024 * 1024), 2),
        "status": 1, # default status 
        "createdBy": userId,
    }
    record = save_image(db, values)
    
    return { "id": record.id, "title": record.title, "imagePath": record.image_url }



def gallery_response(db,obj):
    # FORCE LOAD RELATIONSHIPS
    db.refresh( obj, attribute_names=["created_by_user", "updated_by_user"])
    return {
        "id": obj.id,
        "title": obj.title,
        "imagePath": obj.imagePath,

        # "createdAt": obj.createdAtFormatted,
        # "createdBy": (obj.created_by_user.admin_name if obj.created_by_user else None),
        # "updatedAt": obj.updatedAtFormatted,
        # "updatedBy": (obj.updated_by_user.admin_name if obj.updated_by_user else None),
        # "status": obj.status
    }

def galleryList(db, payload: dict):
    search = payload.get("search", "")
    limit = payload.get("limit", 10)
    offset = payload.get("offset", 0)
    order = payload.get("order", "DESC")

    query = db.query(AdminGallery).filter(AdminGallery.status == 1)

    if search:
        query = query.filter(AdminGallery.title.ilike(f"%{search}%"))

    query = query.order_by(
        AdminGallery.id.desc() if order.upper() == "DESC" else AdminGallery.id.asc()
    )
    total = query.count()
    records = query.offset(offset).limit(limit).all()

    for record in records: 
        record.imagePath = record.image_url

    return { "total": total, "records" : records}

