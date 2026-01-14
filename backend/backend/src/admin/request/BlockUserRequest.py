from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class BlockUserRequest(BaseModel):
    user_id: str = Field(...)
    block_type: str = Field(...)
    custom_until: Optional[date] = Field(None)
