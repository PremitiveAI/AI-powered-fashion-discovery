from sqlalchemy import Column, Integer, String, DateTime, func
from app.database.connection import Base


class UserProfileTable(Base):
    __tablename__ = "tbl_user_profiles"

    id = Column(Integer, primary_key=True, index=True)

    imageUrl = Column(String(255), nullable=True)

    status = Column(Integer, nullable=False, default=1)

    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())
