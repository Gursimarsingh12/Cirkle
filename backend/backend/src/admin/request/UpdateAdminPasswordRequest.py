from pydantic import BaseModel, Field


class UpdateAdminPasswordRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=20)
    old_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
