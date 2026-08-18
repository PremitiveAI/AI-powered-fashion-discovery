import os
import shutil
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.profile_model import ProfileTable
from app.models.otp_model import UserOTPTable
from app.config.env import env

UPLOAD_FOLDER = "uploads/user_photo"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class ProfileController:

    # REGISTER (NO PASSWORD)
    def register(self, db: Session, name, mobile, email):

        existing = db.query(ProfileTable).filter(
            ProfileTable.mobile == mobile
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Mobile already registered")

        profile = ProfileTable(
            name=name,
            mobile=mobile,
            email=email,
            password=None  # Explicit null
        )

        db.add(profile)
        db.commit()
        db.refresh(profile)

        return {
            "message": "Registered successfully",
            "profile_id": profile.id
        }

    # UPLOAD PHOTO
    def upload_photo(self, db: Session, profile_id: int, file: UploadFile):

        profile = db.query(ProfileTable).filter(
            ProfileTable.id == profile_id
        ).first()

        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        file_path = f"{UPLOAD_FOLDER}/{profile_id}_{file.filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        profile.photo = file_path
        db.commit()

        return {"message": "Photo uploaded successfully"}

    # SEND OTP (UAT = 1111)
    def send_otp(self, db: Session, mobile: str):

        otp_entry = UserOTPTable(
            mobile=mobile,
            otp=1111
        )

        db.add(otp_entry)
        db.commit()

        return {
            "message": "OTP sent",
            "otp": 1111  # remove in production
        }

    # VERIFY OTP LOGIN
    def verify_otp(self, db: Session, mobile: str, otp: int):

        if otp != 1111:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        profile = db.query(ProfileTable).filter(
            ProfileTable.mobile == mobile
        ).first()

        if not profile:
            raise HTTPException(status_code=404, detail="User not registered")

        output_path = profile.photo or ""

        return {
            "message": "Login successful",
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "mobile": profile.mobile,
                "email": profile.email,
                "photo": f"{env('BASE_URL')}{output_path}" if output_path else None,
                "status": profile.status,
                "createdAt": profile.createdAt,
                "updatedAt": profile.updatedAt
            }
        }
