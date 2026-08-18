from sqlalchemy import Column, Integer, String, DateTime, func
from app.database.connection import Base


class ProfileTable(Base):
    __tablename__ = "tbl_profiles"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=True)
    mobile = Column(String(15), nullable=False, unique=True, index=True)
    email = Column(String(150), nullable=True)
    password = Column(String(255), nullable=True)

    photo = Column(String(255), nullable=True)

    status = Column(Integer, nullable=False, default=1)

    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())
