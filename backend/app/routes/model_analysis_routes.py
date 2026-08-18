from fastapi import APIRouter, UploadFile, File, Depends, Form,HTTPException, Request,Body
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.controllers.model_analysis_controller import upload_and_analyze_model,get_prompt_and_photo,generate_gemini_image
from app.docs.swagger_headers import SwaggerAPIHeaders


model_router = APIRouter(
    prefix="/model",
    dependencies=[Depends(SwaggerAPIHeaders)]
)

@model_router.post("/upload", tags=["Model Analysis"])
def upload_model(
    file: UploadFile = File(...),
    user_url: str = Form(None),
    db: Session = Depends(get_db)
):
    return upload_and_analyze_model(db, file, user_url)

@model_router.post("/fetchData", tags=["Model Analysis"])
def upload_user_image(
    profileId: int = Body(..., embed=True),
    modelId: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    return get_prompt_and_photo(db, profileId, modelId)

@model_router.post("/uploadUserImage",tags=["Model Analysis"])
async def upload_user_image(
    profileId: int = Body(..., embed=True),
    modelId: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    return await generate_gemini_image(db, profileId, modelId)
