from fastapi import APIRouter, Request, Response, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.docs.swagger_headers import SwaggerAPIHeaders, SwaggerSessionHeaders
# from app.middlewares.auth_middleware import verify_admin_session

from app.schemas.product_schema import productListReq, productSaveReq, galleryList
from app.controllers.product_controller import ProductController

from app.services.product_service import ProductService


# Public Routes (No Session Required)
public_router = APIRouter(
    prefix="/product", tags=["Products"],
    dependencies=[Depends(SwaggerAPIHeaders)]  # SHOW HEADERS IN SWAGGER
)

gallery_router = APIRouter(
    prefix="/gallery", tags=["Gallery"],
    dependencies=[Depends(SwaggerAPIHeaders)]  # SHOW HEADERS IN SWAGGER
)

# Protected Routes (Session Required)
# protected_router = APIRouter(
#     prefix="/user", tags=["User"],
#     dependencies=[Depends(SwaggerSessionHeaders), Depends(verify_session)]
# )


# ADD / UPDATE
@public_router.post("/save")
def create_product(payload: productSaveReq, request: Request, db: Session = Depends(get_db)):
    return ProductController.save(db, payload, request)


@public_router.post("/list")
def list_product(payload: productListReq, request: Request, db: Session = Depends(get_db)):
    return ProductController.list(db, payload, request)

@public_router.get("/get/{product_Id}")
def get_product(product_Id: int, request: Request, db: Session = Depends(get_db)):
    return ProductController.get(db, product_Id, request)


@public_router.delete("/delete/{product_Id}")
def delete_product(product_Id: int, request: Request, db: Session = Depends(get_db)):
    return ProductController.delete(db, product_Id, request)


@public_router.post("/search")
async def product(file: UploadFile = File(...), request: Request = None, db: Session = Depends(get_db)):
    return await ProductController.search(db, request, file)


@gallery_router.post("/upload")
async def upload_images(files: List[UploadFile] = File(...), request: Request = None, db: Session = Depends(get_db)):
    return await ProductController.upload(db, request, files)


@gallery_router.post("/list")
async def list_images(payload: galleryList, request: Request, db: Session = Depends(get_db)):
    return ProductController.gallerylist(db, payload, request)


@public_router.post("/historylist")
def search_history(payload: productListReq,db: Session = Depends(get_db)):
    return ProductService.list_search_history(db, payload)