from pydantic import BaseModel
from typing import Dict, Optional, List
from enum import Enum # Define allowed gender values  
class GenderEnum(str, Enum): 
    male = "male" 
    female = "female"
    other = "other"
class ProductFilter(BaseModel): 
    category_id: Optional[int] = None 
    # define the actual key you want
class productListReq(BaseModel):
    search: Optional[str] = ""
    filter: Optional[ProductFilter] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    sort: Optional[str] = "createdAt"
    order: Optional[str] = "DESC"
    limit: Optional[int] = 10
    offset: Optional[int] = 0
class productSaveReq(BaseModel):
    id: Optional[int]
    hsn_code: Optional[str]
    product_code: Optional[str]
    name: str
    price: float
    mrp:float
    category_id: int
    # subcategory_id: int
    gender: GenderEnum
    brand_id: List[int]
    color_id: List[int]
    images: List[int]
    pattern_id:Optional[int] # 🔥 new 
    subtype_id: Optional[int] # 🔥 new
    product_intro: Optional[str]
    description: Optional[str]
    specification: Optional[str]
    status: int = 1
class galleryList(BaseModel):
    search: Optional[str] = ""
    sort: Optional[str] = "createdAt"
    order: Optional[str] = "DESC"
    limit: Optional[int] = 10
    offset: Optional[int] = 0


