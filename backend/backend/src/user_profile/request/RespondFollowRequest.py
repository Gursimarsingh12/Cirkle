from pydantic import BaseModel, Field


class RespondFollowRequest(BaseModel):
    accept: bool = Field(...)
