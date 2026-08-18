# app/routes/routes.py
from fastapi import APIRouter, UploadFile,Depends
from app.services.decision_models_engine import analyze_image
from app.docs.swagger_headers import SwaggerAPIHeaders

# router = APIRouter()

public_router = APIRouter(
    prefix="/product", tags=["Products"],
    dependencies=[Depends(SwaggerAPIHeaders)]  # SHOW HEADERS IN SWAGGER
)

@public_router.post("/analyze",tags=["Products"])
async def analyze(file: UploadFile):
    """
    Upload an image and analyze it using YOLO for detection,
    Gemini for attributes, and Vision for fallback.
    """
    if not file:
        return error_response("No files uploaded", code=4000)
    contents = await file.read()

    return await analyze_image(contents)

