from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.connection import Base


class ModelTable(Base):
    __tablename__ = "tbl_models"

    id = Column(Integer, primary_key=True, index=True)

    model_name = Column(String(255), nullable=False)
    modle_url = Column(Text, nullable=False)
    prompt = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("tbl_category_models.id"), nullable=False)

    gender = Column(String(10), nullable=True)
    status = Column(Boolean, default=True)

    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    types = relationship("ModelTypeTable", back_populates="model", cascade="all, delete")
    try_ons = relationship("ModelTryOnTable", back_populates="model", cascade="all, delete")
    category = relationship("CategoryModelTable")


class ModelTryOnTable(Base):
    __tablename__ = "tbl_models_try_on"

    id = Column(Integer, primary_key=True, index=True)

    models_id = Column(Integer, ForeignKey("tbl_models.id", ondelete="CASCADE"), nullable=False)
    user_url = Column(Text, nullable=False)

    status = Column(Boolean, default=True)

    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    model = relationship("ModelTable", back_populates="try_ons")


class ModelTypeTable(Base):
    __tablename__ = "tbl_models_type"

    id = Column(Integer, primary_key=True, index=True)

    models_id = Column(Integer, ForeignKey("tbl_models.id", ondelete="CASCADE"), nullable=False)

    category = Column(String(100), nullable=True)
    type = Column(String(100), nullable=True)
    subtype = Column(String(100), nullable=True)
    color = Column(String(100), nullable=True)
    pattern = Column(String(100), nullable=True)
    brand = Column(String(150), nullable=True)
    gender = Column(String(10), nullable=True)

    status = Column(Boolean, default=True)

    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    updatedAt = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    model = relationship("ModelTable", back_populates="types")

