from typing import List
from pydantic import BaseModel, Field
from user_profile.response.FollowRequestResponse import FollowRequestResponse


class NewFollowersPaginatedResponse(BaseModel):
    new_followers: List[FollowRequestResponse] = Field(...)
    page: int = Field(...)
    page_size: int = Field(...)
    total: int = Field(...)
