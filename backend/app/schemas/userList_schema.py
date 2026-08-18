from pydantic import BaseModel
from typing import Optional,Dict,Any

class UserListRequest(BaseModel):
    search: Optional[str] = ""
    # filter: Optional[str] = ""
    filter: Optional[Dict[str, Any]] = {}   # 🔥 CHANGE HERE
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    sort: Optional[str] = "createdAt"
    order: Optional[str] = "DESC"
    limit: Optional[int] = 10
    offset: Optional[int] = 0

