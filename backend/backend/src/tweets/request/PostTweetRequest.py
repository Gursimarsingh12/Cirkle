from typing import Literal
from pydantic import BaseModel, field_validator
from core.exceptions import ValidationError


class PostTweetRequest(BaseModel):
    media_type: Literal["image/jpeg", "image/png", "image/jpg", "image/webp"]

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, v):
        allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
        if v not in allowed_types:
            raise ValidationError(f"Media type must be one of {allowed_types}")
        return v
