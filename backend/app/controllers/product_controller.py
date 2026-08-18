
from fastapi import UploadFile, Request 
from sqlalchemy.orm import Session
from typing import List
from enum import Enum
import json

# from app.models.feature_type_model import FeatureTypeMaster
from app.models.pattern_model import MasterPatterns
from app.models.products_model import Products
from app.models.subtype_model import MasterSubTypes
from app.services.product_service import ProductService, list_to_comma_string

from app.services.gallery_service import process_single_file,  galleryList, gallery_response , save_local_file2
from app.utils.response import success_response, error_response
from app.models.master_categories_model import MasterCategories
from app.models.master_brands_model import MasterBrands
from app.models.master_colors_model import MasterColors
from app.models.admin_gallery_model import AdminGallery

from app.services.decision_engine import analyze_image
from app.services.photo_service import gemini_is_safe_tryon



class ProductController:

    @staticmethod
    def save(db: Session, payload, request: Request):
        data = payload.dict()  # Convert Pydantic model to dict

        data["gender"] = data["gender"].value if isinstance(data["gender"], Enum) else str(data["gender"])

        # Safely get admin user id from request.state, default to 1 if not set 
        admin_id = getattr(request.state, "adminUserId", 1)


        category = db.query(MasterCategories).filter(MasterCategories.id == payload.category_id).first() 
        if not category: 
            return error_response(f"Category with id {payload.category_id} does not exist", code=4000)
        
        # subtypes = db.query(MasterSubTypes.id).filter(MasterSubTypes.id == (payload.subtype_id)).first()
        # if not subtypes:
        #     return error_response(f"Subtype with id {payload.subtype_id} does not exist", code=4000)
        
                   
        # patterns = db.query(MasterPatterns.id).filter(MasterPatterns.id == (payload.pattern_id)).first()
        # if not patterns:
        #     return error_response(f"Pattern with id {payload.pattern_id} does not exist", code=4000)    
        # --- VALIDATE SUBTYPE (Optional) ---
        if payload.subtype_id:
            subtype_exists = db.query(MasterSubTypes.id).filter(MasterSubTypes.id == payload.subtype_id).first()
            if not subtype_exists:
                return error_response(f"Subtype with id {payload.subtype_id} does not exist", code=4000)
        else:
            data["subtype_id"] = None

        # --- VALIDATE PATTERN (Optional) ---
        if payload.pattern_id:
            pattern_exists = db.query(MasterPatterns.id).filter(MasterPatterns.id == payload.pattern_id).first()
            if not pattern_exists:
                return error_response(f"Pattern with id {payload.pattern_id} does not exist", code=4000)
        else:
            data["pattern_id"] = None
        
        existing_brands = ( db.query(MasterBrands.id) .filter(MasterBrands.id.in_(payload.brand_id)) .all() ) 
        existing_colors = ( db.query(MasterColors.id) .filter(MasterColors.id.in_(payload.color_id)) .all() )  
        existing_images = ( db.query(AdminGallery.id) .filter(AdminGallery.id.in_(payload.images)) .all() ) 

        # existing_subtype_ids = {s.id for s in existing_subtypes}
        # existing_pattern_ids = {p.id for p in existing_patterns}
        existing_brand_ids = {b.id for b in existing_brands} 
        existing_color_ids = {b.id for b in existing_colors} 
        existing_image_ids = {b.id for b in existing_images} 

        
        # Find missing IDs 
        # missing_patterns = set(payload.pattern_id) - existing_pattern_ids
        # if missing_patterns:
        #     return error_response(f"Pattern IDs {list(missing_patterns)} do not exist", code=4000)
        
        # missing_subtypes = set(payload.subtype_id) - existing_subtype_ids
        # if missing_subtypes:
        #     return error_response(f"Subtype IDs {list(missing_subtypes)} do not exist", code=4000)
        
    
        missing_ids = set(payload.brand_id) - existing_brand_ids 
        if missing_ids: 
            return error_response(f"Brand IDs {list(missing_ids)} do not exist", code=4000)
        
        missing_idss = set(payload.color_id) - existing_color_ids 
        if missing_idss: 
            return error_response(f"Color IDs {list(missing_idss)} do not exist", code=4000)
        
        missing_idsss = set(payload.images) - existing_image_ids 
        if missing_idsss: 
            return error_response(f"Image IDs {list(missing_idsss)} do not exist", code=4000)
        
        # data["pattern_id"] = list_to_comma_string(payload.pattern_id)
        # data["subtype_id"] = list_to_comma_string(payload.subtype_id)
        data["brand_id"] = list_to_comma_string(payload.brand_id) 
        data["color_id"] = list_to_comma_string(payload.color_id) 
        data["images"] = list_to_comma_string(payload.images) 
        

        if payload.id:
            # Update existing record
            data["updatedBy"] = admin_id
            return ProductService.update_master(db, Products, data, admin_id)

        # Create new record
        data["createdBy"] = admin_id
        return ProductService.create_master(db, Products, data, admin_id)

    @staticmethod
    def list(db: Session, payload, request: Request):
        data = ProductService.list_master(db, Products, payload.dict())
        # print("DATA:", data)
        return success_response( "List fetched successfully",{ 
                "totalRecords": data["total"],
                "list": data["list"]
            }
        )

    @staticmethod
    def get(db: Session, id: int, request: Request):
        return ProductService.get_master_by_id(db, Products, id)

    @staticmethod
    def delete(db: Session, id: int, request: Request):
        admin_id = 1 # request.state.adminUserId
        return ProductService.delete(db, Products, id, updatedBy=admin_id)

   
    @staticmethod
    async def search(db: Session, request: Request, file: UploadFile):
        if not file:
            return error_response("No files uploaded", code=4000)
        admin_id = getattr(request.state, "adminUserId", 1)
        # Read file contents once 
        contents = await file.read()

        if not gemini_is_safe_tryon(contents):
            return error_response(
                "Invalid image: nudity or unsafe content detected",
                code=4002
            )

        # Analyze image using contents 
        data = await analyze_image(contents) # update analyze_image to accept bytes 
        search_data = data.get("data", [])

        enriched_data = []
        for s_data in search_data:
            
            print("SEARCH DATA ITEM ====================> ", s_data["items"])
            s_data["items"] = ProductService.search_products_for_items(s_data["items"])
            enriched_data.append(s_data)

        # save history
        image_path = save_local_file2(admin_id, file.filename, contents, False) 
        ProductService.save_history(db, image_path, enriched_data, admin_id)

        return success_response("Files uploaded successfully",  enriched_data )


    # ============================================================
    # MULTI FILE UPLOAD
    # ============================================================
    @staticmethod
    async def upload(db: Session, request: Request, files: List[UploadFile]):
        if not files:
            return error_response("No files uploaded", code=4000)
        admin_id = getattr(request.state, "adminUserId", 1)

        results, failed = [], []

        for file in files:
            try:
                result = await process_single_file(db, admin_id, file)
                results.append(result)
            except Exception as e:
                failed.append({
                    "filename": file.filename,
                    "ercategoryror": str(e)
                })

        return success_response("Files uploaded successfully", {
            "uploaded": len(results),
            "failed": len(failed),
            "results": results,
            "errors": failed
        })

    @staticmethod
    def gallerylist(db: Session, payload, request: Request):
        data =  galleryList(db, payload.dict())
        return success_response("List fetched successfully",{
            "totalRecords": data['total'],
            "list": [gallery_response(db,r) for r in data['records']]
        })