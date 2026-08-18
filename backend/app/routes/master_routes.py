from fastapi import APIRouter, Depends,Request
from sqlalchemy.orm import Session
from app.database.connection import get_db

from app.schemas.user_schema import UserListReq
from app.schemas.master_schema import Category, SubCategory

from app.controllers.master_controller import MasterController

from app.docs.swagger_headers import SwaggerAPIHeaders, SwaggerSessionHeaders
# from app.middlewares.auth_middleware import verify_admin_session

master_router = APIRouter(
    prefix="/master", #tags=["Master Masters"],
    dependencies=[Depends(SwaggerAPIHeaders)]  # SHOW HEADERS IN SWAGGER
)

# # ---------------- CATEGORY MASTER ----------------

# # ADD / UPDATE
@master_router.post("/category/save" , tags=["Master Category"])
def save_category(payload: Category, request: Request, db: Session = Depends(get_db)):
    return MasterController.save_category_type(db, payload, request)

# LIST
@master_router.post("/category/list", tags=["Master Category"])
def category_list(payload: UserListReq, db: Session = Depends(get_db)):
    return MasterController.list_category_types_post(db,payload)

# # # DELETE
@master_router.delete("/category/delete/{id}", tags=["Master Category"])
def category_delete(id: int,request: Request,db: Session = Depends(get_db)):
    return MasterController.delete_category_type(db, id, request)

# # # GET BY ID
@master_router.get("/category/details/{id}", tags=["Master Category"])
def category_details(id: int, db: Session = Depends(get_db)):
    return MasterController.get_category_type(db, id)

#-----------------------SubType MASTER ----------------------
# # ADD / UPDATE
@master_router.post("/subtype/save", tags=["Master SubType"])
def save_subtype(payload: Category, request: Request, db: Session = Depends(get_db)):
    return MasterController.save_subtype(db, payload, request)
# LIST
@master_router.post("/subtype/list", tags=["Master SubType"])
def subtype_list(payload: UserListReq, db: Session = Depends(get_db)):
    return MasterController.list_subtype(db,payload)

# # # DELETE
@master_router.delete("/subtype/delete/{id}", tags=["Master SubType"])
def subtype_delete(id: int,request: Request,db: Session = Depends(get_db)):
    return MasterController.delete_subtype(db, id, request)

# # # GET BY ID
@master_router.get("/subtype/details/{id}", tags=["Master SubType"])
def subtype_details(id: int, db: Session = Depends(get_db)):
    return MasterController.get_subtype(db, id)

# ---------------- SUBCATEGORY MASTER ----------------
# @master_router.post("/subcategory/save", tags=["Master SubCategory"])
# def save_subcategory(payload: SubCategory, request: Request, db: Session = Depends(get_db)):
#     return MasterController.save_subcategory_type(db, payload, request)

# @master_router.delete("/subcategory/delete/{id}", tags=["Master SubCategory"])
# def subcategory_delete(id: int,request: Request,db: Session = Depends(get_db)):
#     return MasterController.delete_subcategory_type(db, id, request)

# @master_router.post("/subcategory/list", tags=["Master SubCategory"])
# def subcategory_list(payload: UserListReq,db: Session = Depends(get_db)):
#     return MasterController.list_subcategory_types_post(db,payload)

# @master_router.get("/subcategory/details/{id}" , tags=["Master SubCategory"])
# def subcategory_details(id: int, db: Session = Depends(get_db)):
#     return MasterController.get_subcategory_type(db, id)

# ---------------- COLOR MASTER ----------------
@master_router.post("/color/save", tags=["Master Color"])
def save_color(payload: Category, request: Request, db: Session = Depends(get_db)):
    return MasterController.save_color(db, payload, request)

# LIST
@master_router.post("/color/list",tags=["Master Color"])
def color_list(payload: UserListReq,db: Session = Depends(get_db)):
    return MasterController.list_color(db,payload)

# # # DELETE
@master_router.delete("/color/delete/{id}", tags=["Master Color"])
def color_delete(id: int,request: Request,db: Session = Depends(get_db)):
    return MasterController.delete_color(db, id, request)

# # # GET BY ID
@master_router.get("/color/details/{id}", tags=["Master Color"])
def color_details(id: int, db: Session = Depends(get_db)):
    return MasterController.get_color(db, id)


# # ---------------- BRAND MASTER ----------------
@master_router.post("/brand/save", tags=["Master Brand"])
def save_brand(payload: Category, request: Request, db: Session = Depends(get_db)):
    return MasterController.save_brand(db, payload, request)

# LIST
@master_router.post("/brand/list", tags=["Master Brand"])
def brand_list(payload: UserListReq,db: Session = Depends(get_db)):
    return MasterController.list_brand(db,payload)

# # # DELETE
@master_router.delete("/brand/delete/{id}", tags=["Master Brand"])
def brand_delete(id: int,request: Request,db: Session = Depends(get_db)):
    return MasterController.delete_brand(db, id, request)

# # # GET BY ID
@master_router.get("/brand/details/{id}", tags=["Master Brand"])
def brand_details(id: int, db: Session = Depends(get_db)):
    return MasterController.get_brand(db, id)

# # ---------------- PATTERN MASTER ----------------
@master_router.post("/pattern/save", tags=["Master Pattern"])
def save_pattern(payload: Category, request: Request, db: Session = Depends(get_db)):
    return MasterController.save_pattern(db, payload, request)

# LIST
@master_router.post("/pattern/list", tags=["Master Pattern"])
def pattern_list(payload: UserListReq,db: Session = Depends(get_db)):
    return MasterController.list_pattern(db,payload)

# # # DELETE
@master_router.delete("/pattern/delete/{id}", tags=["Master Pattern"])
def pattern_delete(id: int,request: Request,db: Session = Depends(get_db)):
    return MasterController.delete_pattern(db, id, request)

# # # GET BY ID
@master_router.get("/pattern/details/{id}", tags=["Master Pattern"])
def pattern_details(id: int, db: Session = Depends(get_db)):
    return MasterController.get_pattern(db, id)


# LIST
@master_router.post("/product/list",tags=["Master Product"])
def product_list(payload:UserListReq,db: Session = Depends(get_db)):
    return MasterController.list_product(db,payload)
