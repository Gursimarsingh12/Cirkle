from typing import List, Optional
from pydantic import BaseModel, Field


class TopAccount(BaseModel):
    user_id: str = Field(..., description="User's unique ID")
    name: str = Field(..., description="User's display name")
    photo: Optional[str] = Field(
        None, description="Path to user's profile photo on server"
    )
    followers_count: int = Field(..., description="Number of followers")
    is_organizational: bool = Field(
        ..., description="Whether the user is an organizational account"
    )
    is_prime: bool = Field(..., description="Whether the user has prime status")


class TopAccountsResponse(BaseModel):
    accounts: List[TopAccount] = Field(...)
