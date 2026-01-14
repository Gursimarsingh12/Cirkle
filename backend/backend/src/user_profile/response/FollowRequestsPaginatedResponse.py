from typing import List, Any
from pydantic import BaseModel, Field
from user_profile.response.FollowRequestResponse import FollowRequestResponse


class FollowRequestsPaginatedResponse(BaseModel):
    follow_requests: List[FollowRequestResponse] = Field(...)
    page: int = Field(...)
    page_size: int = Field(...)
    total: int = Field(...)
