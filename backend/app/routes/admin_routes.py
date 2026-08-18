# app/routes/login_routes.py

from fastapi import APIRouter, Response, Depends # <-- FIXED: added Header
from fastapi import APIRouter, Response, Depends
from sqlalchemy.orm import Session
from app.middlewares.auth_middleware import verify_session
from app.schemas.signup_schema import SignupRequest
from app.schemas.login_schema import LoginRequest
from app.controllers.admin_controller import AdminController
from app.database.connection import get_db
from app.docs.swagger_headers import SwaggerAPIHeaders


# --------------------------
# Public Routes (No Session Required)
# --------------------------
admin_router = APIRouter(
    prefix="/admin_user", tags=["Admin_User"],
    dependencies=[Depends(SwaggerAPIHeaders)]  # SHOW HEADERS IN SWAGGER
)

# # --------------------------
# # Protected Routes (Session Required)
# # --------------------------
# admin_router = APIRouter(
#     prefix="/admin_user", tags=["Admin_User"],
#     dependencies=[Depends(SwaggerSessionHeaders), Depends(verify_session)]
# )

@admin_router.post("/signup")
async def signup(request: SignupRequest, response: Response, db: Session = Depends(get_db)):
    result = AdminController.signup(db, request)
    return result
   
@admin_router.post("/login")
async def login(request: LoginRequest, response: Response, db: Session = Depends(get_db) ):
    result = AdminController.login(db, request)
    return result






