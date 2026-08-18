from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database.connection import Base


class CategoryModelTable(Base):
    __tablename__ = "tbl_category_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    type = Column(Text, nullable=True)
    gallery_id = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    gender = Column(String(10), nullable=False)
    status = Column(Integer, nullable=False, default=1)
    createdat = Column(DateTime, server_default=func.now())
    updatedat = Column(DateTime, server_default=func.now(), onupdate=func.now())
