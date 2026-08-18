from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ModelGalleryBase(BaseModel):
    image_url: str
    type: str
    status: Optional[str] = "active"


class ModelGalleryCreate(ModelGalleryBase):
    pass


class ModelGalleryResponse(ModelGalleryBase):
    id: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        orm_mode = True
