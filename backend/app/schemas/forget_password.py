from pydantic import BaseModel, EmailStr

class ForgotPasswordRequest(BaseModel):
    username_or_email: str
    new_password: str
    confirm_password: str

class userRequest(BaseModel):
    username_or_email: str
    new_password: str

class userResponse(BaseModel):
    username_or_email: str
    new_password: str
    confirm_password: str
    confirm_password1: str