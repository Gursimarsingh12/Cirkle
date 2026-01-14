from pydantic import BaseModel, Field


class LoginAdminRequest(BaseModel):
    user_id: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)
