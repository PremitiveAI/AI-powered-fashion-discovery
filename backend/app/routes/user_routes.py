from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.user_schema import UserCreate, UserResponse
from app.controllers.user_controller import UserController
from app.docs.swagger_headers import SwaggerAPIHeaders, SwaggerSessionHeaders


# Public Routes (No Session Required)
public_router = APIRouter(
    prefix="/user", tags=["User"],
    dependencies=[Depends(SwaggerAPIHeaders)]  # SHOW HEADERS IN SWAGGER
)

# Protected Routes (Session Required)
# protected_router = APIRouter(
#     prefix="/user", tags=["User"],
#     dependencies=[Depends(SwaggerSessionHeaders), Depends(verify_session)]
# )


@public_router.post("/save", response_model=UserResponse)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    return UserController.create_user(db, data)

@public_router.get("/list", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    return UserController.get_all_users(db)

@public_router.get("/get/{userId}", response_model=UserResponse)
def get_user(userId: int, db: Session = Depends(get_db)):
    return UserController.get_user(db, userId)

@public_router.delete("/delete/{userId}")
def delete_user(userId: int, db: Session = Depends(get_db)):
    return UserController.delete_user(db, userId)