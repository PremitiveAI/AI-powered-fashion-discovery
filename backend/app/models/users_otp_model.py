from sqlalchemy import Column, Integer, String, DateTime, func
from app.database.connection import Base
from datetime import datetime

class UserOTPTable(Base):
    __tablename__ = "tbl_users_otps"

    id = Column(Integer, primary_key=True, index=True)
    dialingCode = Column(Integer, nullable=True, default=91)    
    mobile = Column(String(15), nullable=True)
    email = Column(String(150), nullable=True)
    platform = Column(String(100), nullable=True)
    otpType = Column(String(100), nullable=True)
    otp = Column(Integer, nullable=False, default=0)
    failOtpAttempt = Column(Integer, nullable=False, default=0)
    status = Column(Integer, nullable=False, default=1)

    # AUDIT FIELDS
    createdAt = Column(DateTime, server_default=func.now()) # Auto insert
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now()) # Auto update
