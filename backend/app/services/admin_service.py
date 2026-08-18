# app/services/auth_service.py
import base64, hmac, hashlib, json, time, re
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from sqlalchemy import or_
from datetime import timedelta, timezone
from app.models.admin_model import AdminUsers
from app.models.admin_session_model import AdminSessions
from app.utils.response import success_response, error_response
from app.utils.crypto import encrypt_data

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
SECRET_KEY = "MY_SECRET_KEY_123"

@staticmethod
def read_payload(payload: dict):
        return {
            "search": payload.get("search", ""),
            "filter": payload.get("filter", ""),
            "startDate": payload.get("startDate"),
            "endDate": payload.get("endDate"),
            "sort": payload.get("sort", "createdAt"),
            "order": payload.get("order", "DESC"),
            "limit": payload.get("limit", 10),
            "offset": payload.get("offset", 0)
        }
class AdminService:
# ---------------------- Password helpers ----------------------
    @staticmethod
    def hash_password(password: str):
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str):
        return pwd_context.verify(password, hashed_password)
   
# ---------------------- Field Validations ----------------------
    @staticmethod
    def validate_username(username: str):
        # username key is missing
        if username is None:
            return error_response("Username field is required", 4023)
       
        if not username or not username.strip():
            return error_response("Username cannot be blank", 4001)

        username = username.strip()

        if len(username) < 3:
            return error_response("Username must be at least 3 characters", 4002)

        if not re.fullmatch(r"^[A-Za-z0-9_]+( [A-Za-z0-9_]+)*$", username):
            return error_response("Username can contain only letters, numbers, and underscore", 4003)

    @staticmethod
    def validate_mobile(mobilenumber: str):
        # mobile key is missing
        if mobilenumber is None:
            return error_response("Mobile field is required", 4020)

        if not mobilenumber or not mobilenumber.strip():
            return error_response("Mobile number cannot be blank", 4004)

        mobilenumber = mobilenumber.strip()

        if not mobilenumber.isdigit():
            return error_response("Mobile number must contain only digits", 4005)

        if not re.fullmatch(r"^[6-9][0-9]{9}$", mobilenumber):
            return error_response("Mobile number must be exactly 10 digits and start with 6,7,8,9",4006)

    @staticmethod
    def validate_password(password: str):
        # password key is missing
        if password is None:
            return error_response("Password field is required", 4021)

        if not password or not password.strip():
            return error_response("Password cannot be blank", 4007)
        password = password.strip()

        if len(password) < 6:
            return error_response("Password must be at least 6 characters long", 4008)

        if not re.search(r"[A-Z]", password):
            return error_response("Password must contain at least one uppercase letter", 4009)

        if not re.search(r"[a-z]", password):
            return error_response("Password must contain at least one lowercase letter", 4010)

        if not re.search(r"[0-9]", password):
            return error_response("Password must contain at least one digit", 4011)

        if not re.search(r"[!@#$%^&*_\-+]", password):
            return error_response("Password must contain at least one special character",4012)

    @staticmethod
    def validate_email(email: str):
        #email key is missing
        if email is None:
            return error_response("Email field is required", 4024)
        
        if not email or not email.strip():
            return error_response("Email cannot be blank", 4013)
        email = email.strip()

        if "@" not in email or "." not in email:
            return error_response("Invalid email format", 4014)
        
    @staticmethod
    def validate_company_name(name: str):
        if name is None:
            return error_response("companyName field is required", 4001)

        name = name.strip()
        if not name:
            return error_response("companyName cannot be blank", 4002)

        if len(name) < 2:
            return error_response("companyName must be at least 2 characters", 4003)

    @staticmethod
    def validate_country(country: str):
        if country is None:
            return error_response("country field is required", 4004)

        country = country.strip()
        if not country:
            return error_response("country cannot be blank", 4005)

    @staticmethod
    def validate_state(state: str):
        if state is None:
            return error_response("state field is required", 4006)

        state = state.strip()
        if not state:
            return error_response("state cannot be blank", 4007)

    @staticmethod
    def validate_city(city: str):
        if city is None:
            return error_response("city field is required", 4008)

        city = city.strip()
        if not city:
            return error_response("city cannot be blank", 4009)

    @staticmethod
    def validate_pincode(pincode: str):
        if pincode is None:
            return error_response("pincode field is required", 4010)

        pincode = pincode.strip()
        if not pincode:
            return error_response("pincode cannot be blank", 4011)

        if len(pincode) != 6 or not pincode.isdigit():
            return error_response("Invalid pincode", 4012)

# ---------------------- JWT Token ----------------------
    @staticmethod
    def generate_token(username: str, mobile: str):
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "username": username,
            "mobile": mobile,
            "exp": int(time.time()) + 3600
        }

        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

        signature = hmac.new(
            SECRET_KEY.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()

        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    # ---------------------- Signup ----------------------
    @staticmethod
    def create_adminuser(db: Session, admin_name: str, mobile: str, password: str, email: str):

        if not admin_name:
            return error_response("Admin name required")

        if not mobile:
            return error_response("Mobile required")

        if not password:
            return error_response("Password required")

        if not email:
            return error_response("Email required")
        
        existing = db.query(AdminUsers).filter(
            (AdminUsers.mobile == mobile) | (AdminUsers.email  == email )
        ).first()

        if existing:
            return error_response("Mobile or Email already exists")

        hashed = AdminService.hash_password(password)
        new_admin = AdminUsers(admin_name=admin_name, mobile=mobile, password=hashed, email=email, status=1)
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        return success_response(
            "User created successfully",
            {
                "userId": new_admin.userId,
                "admin_name": new_admin.admin_name,
                "mobile": new_admin.mobile,
                "email": new_admin.email,
                "status": new_admin.status
            },
        )
    
     # ---------------- Login ----------------
    @staticmethod
    def login_adminuser(db: Session, mobile: str, password: str):
        # Validate input
        result = AdminService.validate_mobile(mobile)
        if result:
            return result

        result = AdminService.validate_password(password)
        if result:
            return result

        #  Fetch admin user
        adminuser = db.query(AdminUsers).filter(
            AdminUsers.mobile == mobile,
            AdminUsers.status == 1
        ).first()

        if not adminuser:
            return error_response("User not found OR inactive", code=404)

        if not AdminService.verify_password(password, adminuser.password):
            return error_response("Incorrect password", code=505)
        
        # -------- Invalidate previous sessions --------
        db.query(AdminSessions).filter(
            AdminSessions.userId == adminuser.userId,
            AdminSessions.status == 1
        ).update(
            {
                AdminSessions.status: -1
            },
            synchronize_session=False
        )

        # -------- Create new session --------
        # Generate encrypted session token
        token = encrypt_data({
            "userId": adminuser.userId,
            "mobile": adminuser.mobile,
            "role": adminuser.role
        })

        session = AdminSessions(
            userId=adminuser.userId,
            session_token=token,
            sessionType="WEB",
            status=1
        )
        db.add(session)
        db.commit()

        return success_response(
            "Login successful",
            {
                "userId": adminuser.userId,
                "username": adminuser.admin_name,
                "email": adminuser.email,
                "role": adminuser.role,
                "session_token": token,
            }
        )
