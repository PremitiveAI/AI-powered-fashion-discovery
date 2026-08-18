from fastapi import FastAPI, Request 
from fastapi.responses import JSONResponse 
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from app.database.connection import create_all_tables
from app.middlewares import ( exception_handler, request_logger, jwt_error_handler, auth_middleware )


from app.routes.login_routes import public_router, protected_router
from app.routes.master_routes import master_router
from app.routes.store_routes import store_router
from app.routes.product_routes import public_router as product_route, gallery_router
from app.routes.routes import public_router as router
from app.routes.photo_route import photo_router
from app.routes.profile_routes import user_router
from app.routes.model_analysis_routes import model_router
from app.routes.models_routes import models_router

import os
# from app.routes.admin_routes import admin_router
# from app.routes.kyc_routes import public_router as kyc_public_router,  protected_router as kyc_protected_router


app = FastAPI() 

# Middleware 
app.add_middleware(request_logger.RequestLoggingMiddleware) 
app.add_middleware(auth_middleware.UserApiVerifyMiddleware)

# Exception handlers 
exception_handler.register_exception_handlers(app) 
jwt_error_handler.register_jwt_error_handler(app)


app.include_router(photo_router)

app.include_router(public_router)
app.include_router(protected_router)
app.include_router(master_router)
app.include_router(gallery_router)
app.include_router(store_router)
app.include_router(product_route)
# app.include_router(user_router)
app.include_router(models_router)
app.include_router(model_router)
app.include_router(router)


@app.on_event("startup")
def startup_event():
    create_all_tables()

@app.get("/")
def root():
    return {"message": "FastAPI MVC Running"}

os.makedirs("try_on", exist_ok=True)
app.mount("/try_on", StaticFiles(directory="try_on"), name="try_on")

app.mount("/debug", StaticFiles(directory="/tmp/debug_boxes"), name="debug")
app.mount("/crops", StaticFiles(directory="/tmp/person_crops"), name="crops")

app.mount("/storage", StaticFiles(directory="storage"), name="storage")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/models", StaticFiles(directory="models"), name="models")
# app.mount("/debug", StaticFiles(directory="debug"), name="debug")

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "Success": None,
            "Code": 1,
            "Error": {"message": exc.errors()[0]["msg"]}
        }
    )

# test