from pydantic import BaseModel, Field


class ActionResponse(BaseModel):
    success: bool = Field(...)
    message: str = Field(...)
