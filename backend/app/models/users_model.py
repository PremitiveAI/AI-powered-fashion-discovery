# app/models/users_model.py
import uuid
import hashlib
import secrets
import string
from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.database.connection import Base


def generate_encrypted_userId():
    # Generate a random UUID
    raw_id = str(uuid.uuid4())
    # Encrypt/hash it (example using SHA256)
    encrypted_id = hashlib.sha256(raw_id.encode()).hexdigest()
    return encrypted_id

def generate_userId():
    # Generate 12 random alphanumeric characters
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(12))
    # Prefix with U-{} to make total length 16
    return f"U-{random_part}"

class Users(Base):
    __tablename__ = "tbl_users"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(String(100), unique=True, nullable=False, default=generate_userId)

    fullname = Column(String(100), nullable=True)
    username = Column(String(100), nullable=True, unique=False)
    password = Column(String(255), nullable=True)
    mobile = Column(String(10), nullable=True, unique=True, index=True)
    dialingCode = Column(Integer, nullable=True, default=91)
    email = Column(String(150), nullable=False)
    status = Column(Integer, nullable=False, default=1)

    # New Company / Address Fields
    companyName = Column(String(150), nullable=True)
    country = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    address = Column(String(255), nullable=True)
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)
    gst = Column(String(30), nullable=True)
    pan = Column(String(20), nullable=True)

    # AUDIT FIELDS
    createdBy = Column(Integer, nullable=True, default=0)
    createdAt = Column(DateTime, server_default=func.now()) # Auto insert

    updatedBy = Column(Integer, nullable=True, default=0)
    updatedAt = Column(DateTime, server_default=func.now(), onupdate=func.now()) # Auto update

    deletedBy = Column(Integer, nullable=True)
    deletedAt = Column(DateTime, nullable=True)

    # Relationship back to Users
    # sessions = relationship("Sessions", back_populates="user")
    sessions = relationship("Sessions", back_populates="user", cascade="all, delete-orphan")

# 🎯 Custom __repr__ Method Implementation 🎯
    def __repr__(self):
        """
        Returns a concise, unambiguous, and useful string representation
        of the Users object for debugging and logging.
        """
        # We use an f-string to include key attributes
        return (f"<Users(id={self.id}, "
                f"fullname='{self.fullname}', "
                f"email='{self.email}', "
                f"mobile='{self.mobile}', "
                f"username='{self.username}', "
                f"password='{self.password}', "
                f"status={self.status})>")

# Example usage (what you'll see now):
# user = db.query(Users).filter(...).first()
# print(f'user: {user}')

# FORMATTED PROPERTIES (READ-ONLY)
    @property
    def createdAtFormatted(self):
        return (
            self.createdAt.astimezone(IST).strftime("%d-%b-%Y %H:%M:%S")
            if self.createdAt else None
        )
 
    @property
    def updatedAtFormatted(self):
        return (
            self.updatedAt.astimezone(IST).strftime("%d-%b-%Y %H:%M:%S")
            if self.updatedAt else None
        )
 
    @property
    def dobFormatted(self):
        return self.dob.strftime("%d-%b-%Y") if self.dob else None