from sqlalchemy.orm import Session
from app.schemas.user_schema import UserCreate
from app.repositories.user_repository import UserRepository

class UserService:

    @staticmethod
    def create_user(db: Session, data: UserCreate):
        return UserRepository.create(db, data)

    @staticmethod
    def list_users(db: Session):
        return UserRepository.get_all(db)

    @staticmethod
    def get_user(db: Session, userId: int):
        return UserRepository.get_by_id(db, userId)

    @staticmethod
    def delete_user(db: Session, userId: int):
        return UserRepository.delete(db, userId)