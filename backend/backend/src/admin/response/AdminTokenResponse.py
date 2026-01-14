from pydantic import BaseModel, Field


class AdminTokenResponse(BaseModel):
    access_token: str = Field(...)
    refresh_token: str = Field(...)
