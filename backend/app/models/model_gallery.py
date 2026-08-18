from sqlalchemy import Column, Integer, Text, DateTime, func, Enum
from app.database.connection import Base
import enum


class GalleryType(str, enum.Enum):
    category = "category"
    models = "models"


class ModelGallery(Base):
    __tablename__ = "tbl_models_gallery"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(Text, nullable=False)
    type = Column(Enum(GalleryType), nullable=False)
    status = Column(Integer, default=1)  # 1 = active, 0 = deleted
    createdAt = Column("createdat", DateTime(timezone=True), server_default=func.now())
    updatedAt = Column("updatedat", DateTime(timezone=True),server_default=func.now(),onupdate=func.now())

