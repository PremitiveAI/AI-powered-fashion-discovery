from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserCreate
from app.services.user_service import UserService

class UserController:

    @staticmethod
    def create_user(db: Session, data: UserCreate):
        return UserService.create_user(db, data)

    @staticmethod
    def get_all_users(db: Session):
        return UserService.list_users(db)

    @staticmethod
    def get_user(db: Session, userId: int):
        user = UserService.get_user(db, userId)
        if not user:
            raise HTTPException(status_code=404, detail="User Not Found")
        return user

    @staticmethod
    def delete_user(db: Session, userId: int):
        if not UserService.delete_user(db, userId):
            raise HTTPException(404, "User Not Found")
        return {"message": "User Deleted"}