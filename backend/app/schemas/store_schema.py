from pydantic import BaseModel,EmailStr
from typing import Optional, List
        
class StoreCreate(BaseModel):
    
    id: Optional[int] = None   # 🔥 THIS DECIDES CREATE / UPDATE
    store_name: str
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    pincode: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]

    latitude: Optional[float]
    longitude: Optional[float]

    store_type: str      # ONLINE / OFFLINE / BOTH
    website: Optional[str]

    products_id: List[int]   # list input
    
class StoreListRequest(BaseModel):
    search: Optional[str] = None
    store_type: Optional[str] = None      # online / offline / both
    products_id: Optional[List[int]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    sort: Optional[str] = "createdAt"
    order: Optional[str] = "DESC"
    limit: int = 10
    offset: int = 0

