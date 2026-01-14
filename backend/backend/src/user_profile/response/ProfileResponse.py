from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class ProfileResponse(BaseModel):
    user_id: str = Field(..., description="User's unique ID")
    name: str = Field(..., description="User's display name")
    bio: Optional[str] = Field(None, description="User's bio")
    photo: Optional[str] = Field(
        None, description="Path to user's profile photo on server"
    )
    banner: Optional[str] = Field(
        None, description="Path to user's banner image on server"
    )
    is_private: bool = Field(..., description="Whether the user's profile is private")
    is_organizational: bool = Field(
        ..., description="Whether the user is an organizational account"
    )
    is_prime: bool = Field(..., description="Whether the user has prime status")
    is_online: bool = Field(..., description="Whether the user is currently online")
    followers_count: int = Field(..., description="Number of followers")
    following_count: int = Field(..., description="Number of users being followed")
    interests: List[str] = Field(..., description="List of user's interests")
    command: str = Field(
        ..., description="Command associated with the profile response"
    )
    mutual_followers: List[str] = Field(
        default_factory=list, description="List of mutual followers"
    )
    can_view_content: bool = Field(
        False, description="Whether the user can view content"
    )
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last profile update timestamp")
    message: str = Field(..., description="Message to be displayed")
    follow_status: str = Field(
        None,
        description="Follow status between requester and this user (e.g., 'following', 'not_following', 'requested', etc.)",
    )
