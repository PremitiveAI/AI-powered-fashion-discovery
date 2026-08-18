import uuid
import hashlib
import secrets
import string
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from datetime import timedelta, timezone
from app.database.connection import Base

def generate_encrypted_userId():
    raw_id = str(uuid.uuid4())
    encrypted_id = hashlib.sha256(raw_id.encode()).hexdigest()
    return encrypted_id

def generate_userId():
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(12))
    return f"U-{random_part}"

IST = timezone(timedelta())
class AdminUsers(Base):
    __tablename__ = "tbl_admin"

    id = Column(Integer, primary_key=True, index=True)
    # adminId = Column(String(100), unique=True, nullable=False, default=generate_userId)
    name = Column(String(100), nullable=True, unique=False)
    mobile = Column(String(10), nullable=True, unique=True, index=True)
    password = Column(String(255), nullable=True)
    email = Column(String(150), nullable=False)
    role= Column(String(150), nullable=True)
    status = Column(Integer, nullable=False, default=1)

    # AUDIT FIELDS
    createdBy = Column(Integer, nullable=True, default=0)
    createdAt = Column(DateTime, server_default=func.now()) # Auto insert

    updatedBy = Column(Integer, nullable=True, default=0)
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now()) # Auto update

    deletedBy = Column(Integer, nullable=True)
    deletedAt = Column(DateTime, nullable=True) # NULL until deleted