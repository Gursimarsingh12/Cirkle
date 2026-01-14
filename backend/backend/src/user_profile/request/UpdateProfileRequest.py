from typing import Optional
from pydantic import BaseModel, Field, field_validator
from core.exceptions import ValidationError


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="User's display name"
    )
    bio: Optional[str] = Field(None, max_length=150, description="User's bio")
    is_private: Optional[bool] = Field(
        False, description="Whether the user's profile is private"
    )
    interest_ids: Optional[list[int]] = Field(
        None, description="List of interest IDs associated with the user"
    )
    command_id: Optional[int] = Field(
        None, description="Command ID to assign to the user"
    )
    photo_content_type: Optional[str] = Field(
        None,
        description="Content type of the photo (image/jpeg, image/png, image/jpg, image/webp)",
    )
    banner_content_type: Optional[str] = Field(
        None,
        description="Content type of the banner (image/jpeg, image/png, image/jpg, image/webp)",
    )
    photo_bytes: Optional[bytes] = Field(
        None, description="Raw bytes of the uploaded photo file"
    )
    banner_bytes: Optional[bytes] = Field(
        None, description="Raw bytes of the uploaded banner file"
    )

    @field_validator("photo_content_type", "banner_content_type")
    @classmethod
    def validate_content_type(cls, v):
        if v is not None:
            allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
            if v not in allowed_types:
                raise ValidationError(f"Content type must be one of {allowed_types}")
        return v
