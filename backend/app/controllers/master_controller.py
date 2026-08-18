from fastapi import Request
from sqlalchemy.orm import Session

# from app.models.feature_type_model import FeatureTypeMaster
from app.models.master_categories_model import MasterCategories
from app.models.master_sub_categories_model import MasterSubCategories
from app.models.master_colors_model import MasterColors
from app.models.master_brands_model import MasterBrands
from app.models.pattern_model import MasterPatterns
from app.models.products_model import Products

from app.models.subtype_model import MasterSubTypes
from app.services.master_service import MasterService
class MasterController:

    # ================= FEATURE ================

    # @staticmethod
    # def save_feature_type(db: Session, payload, request: Request):
    #     admin_id = request.state.adminUserId

    #     if payload.id:
    #         payload.updatedBy = admin_id
    #         return MasterService.update_master(
    #             db,
    #             FeatureTypeMaster,
    #             payload.dict(),
    #             admin_id
    #         )

    #     payload.createdBy = admin_id
    #     return MasterService.create_master(
    #         db,
    #         FeatureTypeMaster,
    #         payload.dict(),
    #         admin_id
    #     )

    # @staticmethod
    # def list_feature_types_post(db: Session, payload):
    #     return MasterService.list_master(
    #         db,
    #         FeatureTypeMaster,
    #         payload.dict()
    #     )

    # @staticmethod
    # def get_feature_type(db: Session, id: int):
    #     return MasterService.get_master_by_id(
    #         db,
    #         FeatureTypeMaster,
    #         id
    #     )

    # @staticmethod
    # def delete_feature_type(db: Session, id: int, request: Request):
    #     admin_id = request.state.adminUserId
    #     return MasterService.delete_master(
    #         db,
    #         FeatureTypeMaster,
    #         id,
    #         updatedBy=admin_id
    #     )

    # ================= CATEGORY =================
    @staticmethod
    def save_category_type(db: Session, payload, request: Request):
        admin_id = 1 # request.state.adminUserId
        if payload.id:
            payload.updatedBy = admin_id
            return MasterService.update_master(db, MasterCategories, payload.dict(), admin_id)

        payload.createdBy = admin_id
        return MasterService.create_master(db, MasterCategories, payload.dict(), admin_id)

    @staticmethod
    def list_category_types_post(db: Session, payload):
        return MasterService.list_master(db, MasterCategories, payload.dict())

    @staticmethod
    def get_category_type(db: Session, id: int):
        return MasterService.get_master_by_id(db, MasterCategories, id)

    @staticmethod
    def delete_category_type(db: Session, id: int, request: Request):
        admin_id = 1 # request.state.adminUserId
        return MasterService.delete_master(db, MasterCategories, id, updatedBy=admin_id)
    
    @staticmethod
    def save_subcategory_type(db: Session, payload, request: Request):
        admin_id = 1 # request.state.adminUserId
        if payload.id:
            payload.updatedBy = admin_id
            return MasterService.update_master(db, MasterSubCategories, payload.dict(), admin_id)

        payload.createdBy = admin_id
        return MasterService.create_master(db, MasterSubCategories, payload.dict(), admin_id)
    
    @staticmethod
    def list_subcategory_types_post(db: Session, payload):
        return MasterService.list_master(db, MasterSubCategories, payload.dict())
    
    @staticmethod
    def get_subcategory_type(db: Session, id: int):     
        return MasterService.get_master_by_id(db, MasterSubCategories, id)
    
    @staticmethod
    def delete_subcategory_type(db: Session, id: int, request: Request):
        admin_id = 1 # request.state.adminUserId
        return MasterService.delete_master(db, MasterSubCategories, id, updatedBy=admin_id)
    
    @staticmethod
    def save_color(db: Session, payload, request: Request):
        admin_id = 1 # request.state.adminUserId
        if payload.id:
            payload.updatedBy = admin_id
            return MasterService.update_master(db, MasterColors, payload.dict(), admin_id)

        payload.createdBy = admin_id
        return MasterService.create_master(db, MasterColors, payload.dict(), admin_id)
    
    
    @staticmethod
    def list_color(db: Session, payload):
        return MasterService.list_master(db, MasterColors, payload.dict())

    @staticmethod
    def get_color(db: Session, id: int):
        return MasterService.get_master_by_id(db, MasterColors, id)

    @staticmethod
    def delete_color(db: Session, id: int, request: Request):
        admin_id = 1 # request.state.adminUserId
        return MasterService.delete_master(db, MasterColors, id, updatedBy=admin_id)

    
    @staticmethod
    def save_brand(db: Session, payload, request: Request): 
        admin_id = 1 # request.state.adminUserId
        if payload.id:
            payload.updatedBy = admin_id
            return MasterService.update_master(db, MasterBrands, payload.dict(), admin_id)

        payload.createdBy = admin_id
        return MasterService.create_master(db, MasterBrands, payload.dict(), admin_id)
    
    @staticmethod
    def list_brand(db: Session, payload):   
        return MasterService.list_master(db, MasterBrands, payload.dict())
    
    @staticmethod
    def get_brand(db: Session, id: int):
        return MasterService.get_master_by_id(db, MasterBrands, id) 
    
    @staticmethod
    def delete_brand(db: Session, id: int, request: Request):
        admin_id = 1 # request.state.adminUserId
        return MasterService.delete_master(db, MasterBrands, id, updatedBy=admin_id)
    
    @staticmethod
    def save_pattern(db: Session, payload, request: Request): 
        admin_id = 1 # request.state.adminUserId
        if payload.id:
            payload.updatedBy = admin_id
            return MasterService.update_master(db, MasterPatterns, payload.dict(), admin_id)
        payload.createdBy = admin_id
        return MasterService.create_master(db, MasterPatterns, payload.dict(), admin_id)

    @staticmethod
    def list_pattern(db: Session, payload):   
        return MasterService.list_master(db, MasterPatterns, payload.dict())

    @staticmethod
    def get_pattern(db: Session, id: int):
        return MasterService.get_master_by_id(db, MasterPatterns, id) 
    
    @staticmethod
    def delete_pattern(db: Session, id: int, request: Request):
        admin_id = 1 # request.state.adminUserId
        return MasterService.delete_master(db, MasterPatterns, id, updatedBy=admin_id)
    
    @staticmethod
    def list_product(db: Session, payload):   
        return MasterService.list_products_minimal(db, Products, payload.dict())
    
    @staticmethod
    def save_subtype(db: Session, payload, request: Request): 
        admin_id = 1 # request.state.adminUserId
        if payload.id:
            payload.updatedBy = admin_id
            return MasterService.update_master(db, MasterSubTypes, payload.dict(), admin_id)
        payload.createdBy = admin_id
        return MasterService.create_master(db, MasterSubTypes, payload.dict(), admin_id)

    @staticmethod
    def list_subtype(db: Session, payload):   
        return MasterService.list_master(db, MasterSubTypes, payload.dict())

    @staticmethod
    def get_subtype(db: Session, id: int):
        return MasterService.get_master_by_id(db, MasterSubTypes, id) 
    
    @staticmethod
    def delete_subtype(db: Session, id: int, request: Request):
        admin_id = 1 # request.state.adminUserId
        return MasterService.delete_master(db, MasterSubTypes, id, updatedBy=admin_id)
    