# app/services/auth_service.py
import base64, hmac, hashlib, json, time, re, random, uuid, traceback
import os
from datetime import datetime

from typing import List, Union
from sqlalchemy import func, or_,cast, String
from sqlalchemy.orm import Session, selectinload
# from fastapi import HTTPException
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone

from app.models.pattern_model import MasterPatterns
from app.models.subtype_model import MasterSubTypes
from app.models.users_otp_model import UserOTPTable
from app.models.users_model import Users
from app.models.users_session_model import Sessions
from app.models.search_history_model import SearchHistory

from app.models.master_categories_model import MasterCategories
from app.models.master_brands_model import MasterBrands
from app.models.master_colors_model import MasterColors
from app.models.admin_gallery_model import AdminGallery

# from app.repositories.auth_repository import AuthRepository
from app.utils.response import success_response, error_response
# from app.config.env import env
from app.vector.vector_db import save_vector, search_vector, update_vector, delete_vector, filter_search_vector



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

def list_to_comma_string(values: Union[List[int], List[str]]) -> str:
    """
    Convert a list of integers or strings into a comma-separated string.
    Example: [1, 2, 3] -> "1,2,3"
             ["red", "blue"] -> "red,blue"
    """
    if not values:
        return ""
    return ",".join(str(v) for v in values)

def comma_string_to_list(value: str) -> List[str]:
    """
    Convert a comma-separated string into a list of strings.
    Example: "1,2,3" -> ["1", "2", "3"]
             "red,blue" -> ["red", "blue"]
    """
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v]

def _master_response(db, obj, saveVector=False):
    db.refresh( obj, attribute_names=["created_by_user", "updated_by_user"] )
    
    # Convert brand/color/image IDs into lists of dicts     
    # existing_patterns = [{"id": p.id, "name": p.name} for p in db.query(MasterPatterns) .filter(MasterPatterns.id.in_(comma_string_to_list(obj.pattern_id))) .all() ]
    # existing_subtypes = [{"id": s.id, "name": s.name} for s in db.query(MasterSubTypes) .filter(MasterSubTypes.id.in_(comma_string_to_list(obj.subtype_id))) .all() ]
    existing_brands = [ {"id": b.id, "name": b.name} for b in db.query(MasterBrands) .filter(MasterBrands.id.in_(comma_string_to_list(obj.brand_id))) .all() ] 
    existing_colors = [ {"id": c.id, "name": c.name} for c in db.query(MasterColors) .filter(MasterColors.id.in_(comma_string_to_list(obj.color_id))) .all() ] 
    existing_images = [ {"id": i.id, "path": i.image_url} for i in db.query(AdminGallery) .filter(AdminGallery.id.in_(comma_string_to_list(obj.images))) .all() ]
    

    existing_cat_obj = {}
    existing_cat = db.query(MasterCategories).filter(MasterCategories.id.in_(comma_string_to_list(obj.category_id))).first()
    if existing_cat:
        existing_cat_obj = {"id": existing_cat.id, "name": existing_cat.name}
        
    # existing_patterns = {}
    # existing_patterns =db.query(MasterPatterns).filter(MasterPatterns.id.in_(comma_string_to_list(obj.pattern_id))).first()
    # if existing_patterns:
    #     existing_patterns = {"id": existing_patterns.id, "name": existing_patterns.name}
        
    # existing_subtypes = {}
    # existing_subtypes =db.query(MasterSubTypes).filter(MasterSubTypes.id.in_(comma_string_to_list(obj.subtype_id))).first()
    # if existing_subtypes:
    #     existing_subtypes = {"id": existing_subtypes.id, "name": existing_subtypes.name}
    
    # Pattern (single object)
    existing_pattern_obj = {}
    if obj.pattern_id:
        pattern_id = int(obj.pattern_id) if str(obj.pattern_id).isdigit() else None
        if pattern_id:
            existing_pattern = db.query(MasterPatterns).filter(MasterPatterns.id == pattern_id).first()
            if existing_pattern:
                existing_pattern_obj = {"id": existing_pattern.id, "name": existing_pattern.name}

    # Subtype (single object)
    existing_subtype_obj = {}
    if obj.subtype_id:
        subtype_id = int(obj.subtype_id) if str(obj.subtype_id).isdigit() else None
        if subtype_id:
            existing_subtype = db.query(MasterSubTypes).filter(MasterSubTypes.id == subtype_id).first()
            if existing_subtype:
                existing_subtype_obj = {"id": existing_subtype.id, "name": existing_subtype.name}
    
    # ---------------------------
    # Add 'metadata' field here
    # ---------------------------
    metadata = {
        "category": existing_cat_obj,
        "brands": existing_brands,
        "colors": existing_colors,
        "images": existing_images,
        "gender": obj.gender,
        "price": round(float(obj.price), 2),
        "mrp": round(float(obj.mrp), 2),
        "status": obj.status
    }
    
    product =  {    
        "id": obj.id,
        "hsn_code": obj.hsn_code,
        "product_code": obj.product_code,
        "name": obj.name,
        "mrp": round(float(obj.mrp), 2), 
        "price": round(float(obj.price), 2),
        "gender": obj.gender,
        "category": existing_cat_obj,
        "brands": existing_brands,
        "colors": existing_colors,
        "images": existing_images,
        "pattern": existing_pattern_obj,   # 🔥 same style as category
        "subtype": existing_subtype_obj,   # 🔥 same style as category
        "product_intro": obj.product_intro,
        "description": obj.description,
        "specification": obj.specification,
        "createdAt": obj.createdAtFormatted,
        # "createdBy": (obj.created_by_user.admin_name if obj.created_by_user else None),
        "updatedAt": obj.updatedAtFormatted,
        # "updatedBy": (obj.updated_by_user.admin_name if obj.updated_by_user else None),
        "status": obj.status,
    }
    
    if saveVector:
        print(save_vector("products", product))

    return product



class ProductService:

    # ================= CREATE =================
    @staticmethod
    def create_master(db, model, payload: dict, userId: int):
        if not _validate_name(payload.get("name")):
            return error_response("Name is required", 4030)

        obj = model(
            hsn_code = payload.get("hsn_code"),
            product_code = payload.get("product_code"),
            name = payload.get("name").strip(),
            price = payload.get("price"),
            mrp = payload.get("mrp"),
            category_id = payload.get("category_id"),
            subtype_id = payload.get("subtype_id"),
            pattern_id = payload.get("pattern_id"),
            gender = payload.get("gender"),
            brand_id = payload.get("brand_id"),
            color_id = payload.get("color_id"),
            images = payload.get("images"),
            product_intro = payload.get("product_intro"),
            description = payload.get("description"),
            specification = payload.get("specification"),
            status = payload.get("status"),
            createdBy=userId,
            updatedBy=userId
        )

        db.add(obj)
        db.commit()

        # RE-QUERY WITH RELATIONSHIPS
        obj = (
            db.query(model)
            .options(selectinload(model.created_by_user), selectinload(model.updated_by_user))
            .filter(model.id == obj.id)
            .first()
        )
        return success_response("Created successfully",_master_response(db, obj, True))


    # ================= UPDATE =================
    @staticmethod
    def update_master(db, model, payload: dict, userId: int):

        obj = db.query(model).filter(model.id == payload.get("id")).first()
        
        obj.hsn_code = payload.get("hsn_code"),
        obj.product_code = payload.get("product_code"),
        obj.name = payload.get("name").strip(),
        obj.price = payload.get("price"),
        obj.mrp = payload.get("mrp"),
        obj.category_id = payload.get("category_id"),
        obj.gender = payload.get("gender"),
        obj.brand_id = payload.get("brand_id"),
        obj.color_id = payload.get("color_id"),
        obj.pattern_id = payload.get("pattern_id"),
        obj.subtype_id = payload.get("subtype_id"),
        obj.images = payload.get("images"),
        obj.product_intro = payload.get("product_intro"),
        obj.description = payload.get("description"),
        obj.specification = payload.get("specification"),
        obj.status = payload.get("status"),
        obj.updatedBy=userId
        
        db.commit()
        db.refresh(obj)   #THIS LINE IS REQUIRED

        return success_response("Updated successfully",_master_response(db, obj, True))

    # ================= GET BY ID =================
    @staticmethod
    def get_master_by_id(db, model, id: int):
        obj = db.query(model).filter(model.id == id, model.status == 1).first()
        if not obj:
            return error_response("Record not found", 4040)
        return success_response("Details fetched successfully",_master_response(db,obj))

    
    # ================= DELETE =================
    @staticmethod
    def delete(db, model, id: int, updatedBy=None):
        obj = db.query(model).filter(model.id == id).first()

        if not obj or obj.status == -1:
            return error_response("Record not found", 4040)

        obj.status = -1
        obj.updatedBy = updatedBy
        obj.deletedAt = datetime.utcnow()

        db.commit()

        print(delete_vector("products", id))

        return success_response("Deleted successfully")

    
    # ================= LIST =================
   
    @staticmethod
    def list_master(db: Session, model, payload: dict):
        search = payload.get("search", "")
        limit = int(payload.get("limit", 10))
        offset = int(payload.get("offset", 0))
        order = payload.get("order", "DESC").upper()
        sort = payload.get("sort", "createdAt")
        filter_data = payload.get("filter") or {}

        # ✅ category_id filter
        category_id = filter_data.get("category_id")
        if category_id is not None:
            try:
                category_id = int(category_id)   # force to integer
            except ValueError:
                category_id = None

        # Base query
        query = db.query(model).filter(model.status == 1)

        # 🔍 Search by product name
        if search:
            query = query.filter(model.name.ilike(f"%{search}%"))

        # 🔍 Filter by category_id
        if category_id:
            query = query.filter(model.category_id == str(category_id))

        # 📌 Sorting
        sort_column = getattr(model, sort, model.id)
        query = query.order_by(sort_column.desc() if order == "DESC" else sort_column.asc())

        # ✅ Separate count query
        count_query = db.query(func.count(model.id)).filter(model.status == 1)
        if category_id:
            count_query = count_query.filter(model.category_id == str(category_id))
        total = count_query.scalar()

        # 📊 Pagination
        records = query.offset(offset).limit(limit).all()
        print("RECORDS:", records)
        print("TOTAL:", total)
        return  {
                "total": total,
                "list": [_master_response(db, r) for r in records]
            }
        


    # ================= LIST =================
    @staticmethod
    def search_products_for_items(items, collection_name="products"):
        enriched_items = []

        seen = set()
        unique_items = []

        for item in items:
            
            # Build a tuple of the keys you want to check uniqueness on
            key = (item["category"],item["pattern"],item["subtype"],item["type"], item["color"], item["shade"], item["brand"], item["gender"])
            if key not in seen:
                seen.add(key)
                unique_items.append(item)

        # print(unique_items)


        for item in unique_items:

            # Safely parse filters 
            brands = ( 
                [b.strip().lower() for b in item.get("brand", "").split(",")] if item.get("brand") else [] 
            ) 
            # colors = ( 
            #     [c.strip().lower() for c in item.get("color", "").split(",")] if item.get("color") else [] 
            # ) 

            color_part = [c.strip().lower() for c in item.get("color", "").split(",") if c.strip()] if item.get("color") else []
            shade_part = [d.strip().lower() for d in item.get("shade", "").split(",") if d.strip()] if item.get("shade") else []
            colors = color_part + shade_part


            gender = item.get("gender", "").lower() if item.get("gender") else None 
            # category = item.get("category", "").lower() if item.get("category") else None
            category = item.get("type", "").lower() if item.get("type") else None
            subtype = item.get("subtype", "").lower() if item.get("subtype") else None
            pattern = item.get("pattern", "").lower() if item.get("pattern") else None


            # Build query vector (you can use category + gender + brand + color as text)
            query_text = (
                # f"{category} {gender} {' '.join(brands)} {' '.join(colors)}"
                f"product name: {gender} {category} {' '.join(brands)} {' '.join(colors)} / " 
                f"gender: {gender} / " 
                f"category: {category} / " 
                f"subtype: {subtype} / " 
                f"pattern: {pattern} / " 
                f"brands: {', '.join(brands)} / " 
                f"colors: {', '.join(colors)} / "
                )
            print("query_text ===== = = ===> ", query_text)
            results = filter_search_vector(
                query=query_text,
                limit=3,
                brands=brands,
                colors=colors,
                gender=gender,
                categories=category,
                patterns=pattern,
                subtypes=subtype,
                collection_name=collection_name
            )

            for r in results:
                print(r.payload["name"], r.payload["brand_names"], r.payload["color_names"], r.payload["gender"], r.score)

            # Attach results back into item
            item["product_list"] = [{
                    "id": r.payload["id"], 
                    "hsn_code": r.payload["hsn_code"],
                    "product_code": r.payload["product_code"],
                    "name": r.payload["name"],
                    "mrp": r.payload["mrp"],
                    "price": r.payload["price"],
                    "gender": r.payload["gender"],
                    "category": r.payload["category"],
                    "subtype": r.payload.get("subtype", ""), #r.payload["subtype"],
                    "pattern": r.payload.get("pattern", ""), #r.payload["pattern"],
                    "brands": r.payload.get("brand_names", []),
                    "colors": r.payload.get("color_names", []),
                    "images": r.payload.get("images", []),
                    "product_intro": r.payload["product_intro"],
                    "description": r.payload["description"],
                    "specification": r.payload["specification"],
                    "createdAt": r.payload["createdAt"],
                    "updatedAt": r.payload["updatedAt"],
                    "status": r.payload["status"],
                    "score": r.score
                }
                for r in results
            ]

            enriched_items.append(item)

        return enriched_items
    
    # ================= SEARCH HISTORY LIST =================

    @staticmethod
    def list_search_history(db: Session, payload):
        query = db.query(SearchHistory).filter(SearchHistory.status == 1)

        #Search (imagePath / search_result)
        if payload.search:
            query = query.filter(
                or_(
                    SearchHistory.imagePath.ilike(f"%{payload.search}%"),
                    SearchHistory.search_result.ilike(f"%{payload.search}%")
                )
            )

        #Date filter
        if payload.startDate and payload.endDate:
            try:
                start_date = datetime.strptime(payload.startDate, "%Y-%m-%d")
                end_date = datetime.strptime(payload.endDate, "%Y-%m-%d")

                query = query.filter(
                    SearchHistory.createdAt.between(start_date, end_date)
                )
            except ValueError:
                pass  # ignore invalid date format safely

        #Sorting
        sort_column = getattr(SearchHistory, payload.sort, SearchHistory.createdAt)
        if payload.order.upper() == "ASC":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        #Pagination
        total_count = query.count()

        history = (
            query.offset(payload.offset).limit(payload.limit).all()
        )

        data = []
        for item in history:
                    # Open and load JSON
            with open(item.search_result, "r", encoding="utf-8") as f:
                search_result = json.load(f)
            data.append({
                "id": item.id,
                "imagePath": item.image_url,
                "search_result": search_result,
                "createdAt":item.createdAtFormatted
            })

        return success_response("Search history list fetched successfully",{
            "total": total_count,
            "records": data
        } )
    



    # ================= CREATE =================
    @staticmethod
    def save_history(db, image_path, result, userId):

        # Step 1: Save JSON data to file
        folder = "storage"
        os.makedirs(folder, exist_ok=True)

        file_name = f"product_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = os.path.join(folder, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        print(f"✅ JSON saved at {file_path}")
        
        obj = SearchHistory(
            imagePath = image_path,
            search_result = file_path,
            status = 1,
            createdBy=userId,
            updatedBy=userId
        )

        db.add(obj)
        db.commit()

        return True
