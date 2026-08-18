from sqlalchemy import or_,asc, desc
import re
import math
from sqlalchemy.orm import Session
from app.models.stores_model import Stores
from app.models.products_model import Products
from app.utils.response import success_response, error_response


# validation Helpers
def _is_valid_email(email: str) -> bool:
        return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

def _is_valid_phone(phone: str) -> bool:
        return bool(re.match(r"^[6-9]\d{9}$", phone)) 

def _is_valid_pincode(pincode: str) -> bool:
        return bool(re.match(r"^\d{6}$", pincode))

def _is_valid_store_type(store_type: str) -> bool:
        return store_type in ["ONLINE", "OFFLINE"]
    
#calculate distance between two lat/lon points
def calculate_distance_km(lat1, lon1, lat2, lon2):
    if not lat1 or not lon1 or not lat2 or not lon2:
        return None

    R = 6371  # Earth radius in KM

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 2)

def none_if_empty(value):
    if value in [0, "", None]:
        return None
    return value

# validate product ids exist
def validate_product_ids(db: Session, product_ids: list[int]):
    if not product_ids:
        return False, []

    existing_ids = (
        db.query(Products.id)
        .filter(
            Products.id.in_(product_ids),
            Products.status == 1
        )
        .all()
    )

    existing_ids = {row[0] for row in existing_ids}
    invalid_ids = list(set(product_ids) - existing_ids)

    return len(invalid_ids) == 0, invalid_ids


class StoreController:
    
# ================= CREATE / UPDATE STORE =================
    
    @staticmethod
    def save_store(db: Session, payload):
        required_fields = {
        "store_name": payload.store_name,
        "address": payload.address,
        "city": payload.city,
        "state": payload.state,
        "pincode": payload.pincode,
        "phone": payload.phone,
        "email": payload.email,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "store_type": payload.store_type,
        "products_id": payload.products_id
    }
        for field, value in required_fields.items():
            if value is None or (isinstance(value, str) and not value.strip()):
                return error_response(f"{field.replace('_', ' ').title()} is required", 400)

    # ---------------- FORMAT VALIDATION ----------------
        if not _is_valid_email(payload.email):
            return error_response("Invalid email format", 400)

        if not _is_valid_phone(payload.phone):
            return error_response("Invalid phone number", 400)

        if not _is_valid_pincode(payload.pincode):
            return error_response("Invalid pincode", 400)

        if not _is_valid_store_type(payload.store_type):
            return error_response("Store type must be ONLINE, OFFLINE", 400)

        if not isinstance(payload.products_id, list) or len(payload.products_id) == 0:
            return error_response("At least one product is required", 400)

        # ---------- PRODUCT EXISTENCE CHECK ----------
        is_valid, invalid_ids = validate_product_ids(db, payload.products_id)
        if not is_valid:
            return error_response(
                 f"Invalid product id {', '.join(map(str, invalid_ids))}", 400)
       
        
        #UPDATE
        if payload.id:
            store = (
                db.query(Stores)
                .filter(Stores.id == payload.id, Stores.status == 1)
                .first()
            )

            if not store:
                return error_response("Store not found", 404)

            message = "Store updated successfully"

        #CREATE
        else:
            store = Stores()
            db.add(store)
            message = "Store created successfully"

        # COMMON FIELDS
        store.store_name = payload.store_name
        store.address = payload.address
        store.city = payload.city
        store.state = payload.state
        store.pincode = payload.pincode
        store.phone = payload.phone
        store.email = payload.email
        store.latitude = payload.latitude
        store.longitude = payload.longitude
        store.store_type = payload.store_type
        store.website = payload.website

        # Save product ids
        store.products_id = ",".join(map(str, payload.products_id))

        db.commit()
        db.refresh(store)

        return success_response(
            message,
            {
             "store_id": store.id,
             "store_name": store.store_name,
             "store_type": store.store_type,
             "address": store.address,
             "city": store.city,
             "state": store.state,
             "pincode": store.pincode,
             "phone": store.phone,
             "email": store.email,
             "latitude": store.latitude,
             "longitude": store.longitude,
             "website": store.website,
            #  "product_ids": store.products_id,
             "products_id": (
                    list(map(int, store.products_id.split(",")))
                    if store.products_id else []
                ),
             "status": store.status
             }
        )

#  # ================= GET STORE BY ID =================
    @staticmethod
    def get_store_details(db: Session, store_id: int):
        store = (
            db.query(Stores)
            .filter(Stores.id == store_id, Stores.status == 1)
            .first()
        )

        if not store:
            return error_response("Store not found", 404)

        return success_response(
            "Store details fetched",
            {
                "id": store.id,
                "store_name": store.store_name,
                "address": store.address,
                "city": store.city,
                "state": store.state,
                "pincode": store.pincode,
                "phone": store.phone,
                "email": store.email,
                "latitude": store.latitude,
                "longitude": store.longitude,
                "store_type": store.store_type,
                "website": store.website,
                "status": store.status,
                "products_id": (
                    list(map(int, store.products_id.split(",")))
                    if store.products_id else []
                )
            }
        )
        
    # ================= LIST STORES ================= 
    @staticmethod
    def list_stores(db: Session, payload):

        query = db.query(Stores).filter(Stores.status == 1)

    #store_type filter
        if payload.store_type and payload.store_type.strip():
            query = query.filter(
                Stores.store_type == payload.store_type.strip().upper()
            )

    #products filter
        if payload.products_id and len(payload.products_id) > 0:
            product_conditions = []
            for pid in payload.products_id:
                pid = str(pid)
                product_conditions.extend([
                    Stores.products_id == pid,
                    Stores.products_id.like(f"{pid},%"),
                    Stores.products_id.like(f"%,{pid},%"),
                    Stores.products_id.like(f"%,{pid}")
                ])
            query = query.filter(or_(*product_conditions))

        #search
        if payload.search:
            search_text = f"%{payload.search}%"
            query = query.filter(
                or_(
                    Stores.store_name.ilike(search_text),
                    Stores.city.ilike(search_text)
                )
            )

        total_records = query.count()

        stores = (
            query
            .offset(payload.offset)
            .limit(payload.limit)
            .all()
        )

        data = []
        for store in stores:
            if store.store_type == "ONLINE":
                data.append({
                    "id": store.id,
                    "store_name": store.store_name,
                    "store_type": store.store_type,
                    "email": store.email,
                    "website": store.website,
                    "distance_km": None   #ONLINE STORES HAVE NO DISTANCE

                })
            else:
                distance = calculate_distance_km(
                    payload.latitude,
                    payload.longitude,
                    store.latitude,
                    store.longitude
                )
                data.append({
                    "id": store.id,
                    "store_name": store.store_name,
                    "address": store.address,
                    "city": store.city,
                    "state": store.state,
                    "pincode": store.pincode,
                    "phone": store.phone,
                    "latitude": store.latitude,
                    "longitude": store.longitude,
                    "distance_km": distance,
                    "store_type": store.store_type,
                    "website": store.website
                })
         #SORT BY DISTANCE (nearest first)
        if payload.latitude and payload.longitude:
            data.sort(
                key=lambda x: x["distance_km"] if x["distance_km"] is not None else 999999
            )

        return success_response(
            "Store list fetched successfully",
            {
                "totalRecords": total_records,
                "list": data
            }
        )

    # ================= DELETE STORE =================
    @staticmethod
    def delete_store(db: Session, store_id: int):
        store = db.query(Stores).filter(Stores.id == store_id,Stores.status != -1).first()

        if not store:
            return error_response("Store not found", 404)

        store.status = -1
        db.commit()
        return success_response("Store deleted successfully")