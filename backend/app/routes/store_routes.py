from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.store_schema import StoreCreate,StoreListRequest
from app.controllers.store_controller import StoreController
from app.schemas.userList_schema import UserListRequest

from app.docs.swagger_headers import SwaggerAPIHeaders

store_router = APIRouter(
    prefix="/store", tags=["stores"],
    dependencies=[Depends(SwaggerAPIHeaders)]  # SHOW HEADERS IN SWAGGER
)

# ================= CREATE STORE =================
@store_router.post("/save")
def save_store(payload: StoreCreate,db: Session = Depends(get_db)):
    return StoreController.save_store(db, payload)

# # ================= STORE DETAILS =================
@store_router.get("/details/{store_id}")
def store_details(store_id: int, db: Session = Depends(get_db)):
    return StoreController.get_store_details(db, store_id)

# # ================= LIST STORES =================
@store_router.post("/list")
def list_stores(payload: StoreListRequest,db: Session = Depends(get_db)):
    return StoreController.list_stores(db, payload)

# # ================= DELETE STORE =================
@store_router.delete("/delete/{store_id}")
def delete_store(store_id: int, db: Session = Depends(get_db)):
    return StoreController.delete_store(db, store_id)