from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.controllers.profile_controller import ProfileController
from app.schemas.profile_schema import RegisterRequest, SendOtpRequest, VerifyOtpRequest
from app.docs.swagger_headers import SwaggerAPIHeaders

controller = ProfileController()

user_router = APIRouter(
    prefix="/user",
    dependencies=[Depends(SwaggerAPIHeaders)]
)


@user_router.post("/register", tags=["User Details"])
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    return controller.register(
        db,
        request.name,
        request.mobile,
        request.email
    )


@user_router.post("/upload-photo", tags=["User Details"])
def upload_photo(profile_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    return controller.upload_photo(db, profile_id, file)


@user_router.post("/send-otp", tags=["User Details"])
def send_otp(request: SendOtpRequest, db: Session = Depends(get_db)):
    return controller.send_otp(db, request.mobile)


@user_router.post("/verify-otp", tags=["User Details"])
def verify_otp(request: VerifyOtpRequest, db: Session = Depends(get_db)):
    return controller.verify_otp(db, request.mobile, request.otp)
