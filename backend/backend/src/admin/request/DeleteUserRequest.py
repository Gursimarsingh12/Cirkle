from pydantic import BaseModel, Field


class DeleteUserRequest(BaseModel):
    user_id: str = Field(..., description="User ID to delete")
