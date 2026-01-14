from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class FollowRequestResponse(BaseModel):
    follower_id: str = Field(..., description="Follower's user ID")
    name: str = Field(..., description="Follower's display name")
    photo: Optional[str] = Field(
        None, description="Path to follower's profile photo on server"
    )
    created_at: datetime = Field(..., description="Follow request creation timestamp")
    is_private: bool = Field(..., description="Whether the user's profile is private")
    is_prime: bool = Field(..., description="Whether the user has prime status")
    is_organizational: bool = Field(
        ..., description="Whether the user is an organizational account"
    )
