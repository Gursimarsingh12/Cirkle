from pydantic import BaseModel, Field
from typing import Optional


class UserSearchRequest(BaseModel):
    search: Optional[str] = Field(None, description="Search by user_id or name")
    page: int = Field(1, ge=1, description="Page number")
    command_id: Optional[int] = Field(None, description="Filter by command ID")
    is_organizational: Optional[bool] = Field(
        None, description="Filter by organizational users"
    )
    is_private: Optional[bool] = Field(None, description="Filter by private users")
    is_prime: Optional[bool] = Field(None, description="Filter by prime users")
