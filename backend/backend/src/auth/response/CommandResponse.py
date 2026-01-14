from pydantic import BaseModel, Field


class CommandResponse(BaseModel):
    id: int = Field(...)
    name: str = Field(...)
