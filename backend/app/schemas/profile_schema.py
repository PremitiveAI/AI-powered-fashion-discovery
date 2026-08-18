from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    name: str
    mobile: str
    email: EmailStr


class SendOtpRequest(BaseModel):
    mobile: str


class VerifyOtpRequest(BaseModel):
    mobile: str
    otp: int
