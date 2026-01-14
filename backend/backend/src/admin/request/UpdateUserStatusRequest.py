from pydantic import BaseModel, Field
from typing import Optional


class UpdateUserStatusRequest(BaseModel):
    user_id: str = Field(..., description="User ID to update")
    is_prime: Optional[bool] = Field(None, description="Set user as prime or not")
    is_organizational: Optional[bool] = Field(
        None, description="Set user as organizational or not"
    )
