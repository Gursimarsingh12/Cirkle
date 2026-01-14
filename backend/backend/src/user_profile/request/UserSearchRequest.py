from pydantic import BaseModel, Field
from typing import Optional


class UserSearchRequest(BaseModel):
    search: Optional[str] = Field(None, description="Search by user_id or name")
    page: int = Field(1, ge=1, description="Page number")
