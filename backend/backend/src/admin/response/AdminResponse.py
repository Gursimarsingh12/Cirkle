from pydantic import BaseModel, Field


class AdminResponse(BaseModel):
    user_id: str = Field(...)
    is_admin: bool = Field(...)
