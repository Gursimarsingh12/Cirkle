from pydantic import BaseModel, Field
from typing import List, Dict, Any


class UserSearchResponse(BaseModel):
    users: List[Dict[str, Any]] = Field(...)
    total: int = Field(...)
    page: int = Field(...)
    page_size: int = Field(...)
