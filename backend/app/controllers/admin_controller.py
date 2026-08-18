#app/controllers/auth_controller.py
from sqlalchemy.orm import Session
from app.services.admin_service import AdminService

class AdminController:

    # ---------------------- SIGNUP ----------------------
    @staticmethod
    def signup(db: Session, data):
        return AdminService.create_adminuser(
            db=db,
            admin_name=data.username,
            mobile=data.mobile,
            password=data.password,
            email=data.email
        )

    # ---------------------- LOGIN ----------------------
    @staticmethod
    def login(db: Session, data):
        return AdminService.login_adminuser(
            db=db,
            mobile=data.mobile,
            password=data.password
        )

    