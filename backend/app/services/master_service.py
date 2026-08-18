# app/services/auth_service.py
import base64, hmac, hashlib, json, time, re, random, uuid, traceback
from sqlalchemy.orm import Session, selectinload
# from fastapi import HTTPException
from passlib.context import CryptContext
from sqlalchemy import func, or_
from datetime import datetime, timedelta, timezone
from app.models.users_otp_model import UserOTPTable
from app.models.users_model import Users
from app.models.users_session_model import Sessions
from app.models.master_sub_categories_model import MasterSubCategories
from app.models.master_categories_model import MasterCategories
from app.models.products_model import Products
# from app.schemas.userList_schema import UserListRequest



# from app.repositories.auth_repository import AuthRepository
from app.utils.response import success_response, error_response
from app.utils.crypto import encrypt_data, decrypt_data
# from app.config.env import env


IST = timezone(timedelta(hours=5, minutes=30))
# IST = pytz.timezone("Asia/Kolkata")

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

def _validate_name(name):
    return bool(name and str(name).strip())

def _null_if_empty(value):
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value

def _master_response(db,obj):
    # FORCE LOAD RELATIONSHIPS
    db.refresh( obj, attribute_names=["created_by_user", "updated_by_user"] )
    
    cat = {}
    cat['category_id'] = obj.category_id if hasattr(obj, "category_id") else None
    
    data = {
        "id": obj.id,
        "name": obj.name,
        "description": obj.description,
        "createdAt": obj.createdAtFormatted,
        "updatedAt": obj.updatedAtFormatted,
        "status": obj.status,
        # "imageId": obj.imageId,
        # "imagePath": obj.imagePath,
        # "createdBy": (obj.created_by_user.admin_name if obj.created_by_user else None),
        # "updatedBy": (obj.updated_by_user.admin_name if obj.updated_by_user else None),
    }

    if hasattr(obj, "category_id") and obj.category_id is not None and cat is not None: 
        data.update(cat)
    return data   



class MasterService:

    # ================= CREATE =================
    @staticmethod
    def create_master(db, model, payload: dict, userId: int):
        if not _validate_name(payload.get("name")):
            return error_response("Name is required", 4030)

        print(" model:", model)
        obj = model(
            name=payload.get("name").strip(),
            description=_null_if_empty(payload.get("description")),
            # imageId=_null_if_empty(payload.get("imageId")),
            # imagePath=_null_if_empty(payload.get("imagePath")),
            createdBy=userId,
            updatedBy=userId
            
        )
        # ✅ ADD THIS (do not remove anything)
        if hasattr(model, "category_id"):
            obj.category_id = payload.get("category_id")

        db.add(obj)
        db.commit()

        # RE-QUERY WITH RELATIONSHIPS
        obj = (
            db.query(model)
            .options(selectinload(model.created_by_user), selectinload(model.updated_by_user))
            .filter(model.id == obj.id)
            .first()
        )
        return success_response("Created successfully",_master_response(db, obj))

    # ================= UPDATE =================
    @staticmethod
    def update_master(db, model, payload: dict, updatedBy: int):
        obj = db.query(model).filter(model.id == payload.get("id")).first()

        if not obj:
            return error_response("Record not found", 4040)

        if not _validate_name(payload.get("name")):
            return error_response("Name is required", 4030)

        obj.name = payload["name"].strip()
        obj.description = _null_if_empty(payload.get("description"))
        obj.imageId = _null_if_empty(payload.get("imageId"))
        obj.imagePath = _null_if_empty(payload.get("imagePath"))
        obj.updatedBy = updatedBy
        
        # ✅ ADD THIS (do not remove anything)
        if hasattr(model, "category_id"):
            obj.category_id = payload.get("category_id")


        db.commit()
        db.refresh(obj)   #THIS LINE IS REQUIRED

        return success_response("Updated successfully", _master_response(db,obj))

    # ================= GET BY ID =================
    @staticmethod
    def get_master_by_id(db, model, id: int):
        obj = db.query(model).filter(model.id == id, model.status == 1).first()

        if not obj:
            return error_response("Record not found", 4040)

        return success_response("Details fetched successfully", _master_response(db,obj))

    # ================= DELETE =================
    @staticmethod
    def delete_master(db, model, id: int, updatedBy=None):
        obj = db.query(model).filter(model.id == id).first()

        if not obj or obj.status == -1:
            return error_response("Record not found", 4040)

        obj.status = -1
        obj.updatedBy = updatedBy
        obj.deletedAt = datetime.utcnow()

        db.commit()
        return success_response("Deleted successfully")

    # ================= LIST =================
    # @staticmethod
    # def list_master(db, model, payload: dict):
    #     search = payload.get("search", "")
    #     limit = payload.get("limit", 10)
    #     offset = payload.get("offset", 0)
    #     order = payload.get("order", "DESC")
    #     filter = payload.get("filter") or {}
    #     category_id = filter.get("category_id") if filter else None

    #     query = db.query(model).filter(model.status == 1)

    #     # if search:
    #     #     query = query.filter(model.name.ilike(f"%{search}%"))
    #     # 🔥 SPECIAL CASE: SUBCATEGORY SEARCH
    #     if model == MasterSubCategories:
    #         query = query.join(
    #             MasterCategories,
    #             MasterCategories.id == MasterSubCategories.category_id
    #         ).filter(MasterCategories.status == 1)
            
    #         # 🔥 FILTER BY CATEGORY ID
    #         if category_id:
    #             query = query.filter(
    #                 MasterSubCategories.category_id == category_id
    #             )

    #     # 🔍 SEARCH (subcategory OR category)
    #     if search:
    #         query = query.filter(
    #             or_(
    #                 MasterSubCategories.name.ilike(f"%{search}%"),
    #                 MasterCategories.name.ilike(f"%{search}%")
    #             )
    #         )
    #     else:
    #         if search:
    #             query = query.filter(model.name.ilike(f"%{search}%"))

    
    #     query = query.order_by(
    #         model.id.desc() if order.upper() == "DESC" else model.id.asc()
    #     )

    #     total = query.count()
    #     records = query.offset(offset).limit(limit).all()

    #     return success_response(
    #         "List fetched successfully",
    #         {
    #             "totalRecords": total,
    #             "list": [_master_response(db,r) for r in records]
    #         }
    #     )
    @staticmethod
    def list_master(
        db: Session,
        model,
        payload: dict,
        search_columns: list[str] = None,
        join_conditions: list = None,
        extra_filters: list = None
    ):
        """
        Generic list API for master tables.
        
        Args:
            db: SQLAlchemy session
            model: SQLAlchemy model class
            payload: dict with search, limit, offset, order, filter
            search_columns: list of model columns to apply search on
            join_conditions: list of (join_model, condition) tuples
            extra_filters: list of additional filter expressions
        """

        search = payload.get("search", "")
        limit = payload.get("limit", 10)
        offset = payload.get("offset", 0)
        order = payload.get("order", "DESC")
        filter_data = payload.get("filter") or {}

        query = db.query(model).filter(model.status == 1)

        # 🔗 Handle joins if provided
        if join_conditions:
            for join_model, condition in join_conditions:
                query = query.join(join_model, condition).filter(join_model.status == 1)

        # 🔍 Handle filters if provided
        if extra_filters:
            for f in extra_filters:
                query = query.filter(f)

        # 🔍 Search across multiple columns
        if search and search_columns:
            search_filters = [col.ilike(f"%{search}%") for col in search_columns]
            query = query.filter(or_(*search_filters))
        elif search and hasattr(model, "name"):
            query = query.filter(model.name.ilike(f"%{search}%"))

        # 📌 Ordering
        query = query.order_by(
            model.id.desc() if order.upper() == "DESC" else model.id.asc()
        )

        # 📊 Pagination
        total = query.count()
        records = query.offset(offset).limit(limit).all()

        return success_response(
            "List fetched successfully",
            {
                "totalRecords": total,
                "list": [_master_response(db, r) for r in records]
            }
        )

    @staticmethod
    def list_products_minimal(db, model, payload: dict):
      
        search = payload.get("search", "")
        limit = payload.get("limit", 10)
        offset = payload.get("offset", 0)
        order = payload.get("order", "DESC")

        query = db.query(model).filter(model.status == 1)

        if search:
            query = query.filter(model.name.ilike(f"%{search}%"))

        query = query.order_by(
            model.id.desc() if order.upper() == "DESC" else model.id.asc()
        )

        total = query.count()
        records = query.offset(offset).limit(limit).all()

        # Only include id and name
        list_response = [{"id": r.id, "name": r.name} for r in records]

        return success_response(
            "List fetched successfully",
            {
                "totalRecords": total,
                "list": list_response
            }
        )

