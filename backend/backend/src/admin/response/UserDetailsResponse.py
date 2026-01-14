from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class UserDetailsResponse(BaseModel):
    user_id: str = Field(..., description="Unique identifier for the user")
    name: str = Field(..., description="User's display name")
    date_of_birth: date = Field(..., description="User's date of birth")
    is_organizational: bool = Field(
        ..., description="Whether the user is an organizational account"
    )
    is_private: bool = Field(..., description="Whether the user's account is private")
    is_prime: bool = Field(..., description="Whether the user has prime status")
    is_active: bool = Field(..., description="Whether the user's account is active")
    is_online: bool = Field(..., description="Whether the user is currently online")
    is_blocked: bool = Field(..., description="Whether the user is blocked")
    block_until: Optional[date] = Field(
        None, description="Date until which the user is blocked, if applicable"
    )
    command_id: int = Field(..., description="ID of the command the user belongs to")
    photo: Optional[str] = Field(
        None, description="Path to user's profile photo on server"
    )
    banner: Optional[str] = Field(
        None, description="Path to user's banner image on server"
    )
    bio: Optional[str] = Field(None, description="User's bio text")
    created_at: date = Field(..., description="Date when the user account was created")
