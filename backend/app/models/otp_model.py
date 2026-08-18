from sqlalchemy import Column, Integer, String, DateTime, func
from app.database.connection import Base


class UserOTPTable(Base):
    __tablename__ = "tbl_otps"

    id = Column(Integer, primary_key=True, index=True)

    dialingCode = Column(Integer, nullable=True, default=91)
    mobile = Column(String(15), nullable=False)
    otp = Column(Integer, nullable=False, default=1111)

    status = Column(Integer, nullable=False, default=1)

    createdAt = Column(DateTime, server_default=func.now())
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now())
