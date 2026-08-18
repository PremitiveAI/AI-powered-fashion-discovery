from pydantic import BaseModel,EmailStr
from typing import Optional, List

class Category(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    # imageId: Optional[str] = None
    # imagePath: Optional[str] = None
    createdBy: Optional[int] = None
    updatedBy: Optional[int] = None


class SubCategory(BaseModel):
    id: Optional[int] = None
    category_id: int
    name: str
    description: Optional[str] = None
    # imageId: Optional[str] = None
    # imagePath: Optional[str] = None
    createdBy: Optional[int] = None
    updatedBy: Optional[int] = None
    
    
