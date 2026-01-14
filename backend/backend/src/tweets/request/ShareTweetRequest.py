from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from core.exceptions import ValidationError


class ShareTweetRequest(BaseModel):
    tweet_id: int = Field(..., description="ID of the tweet being shared")
    recipient_ids: List[str] = Field(
        ..., 
        min_length=1, 
        max_length=5, 
        description="List of user IDs to share the tweet with (max 5)"
    )
    message: Optional[str] = Field(
        None, max_length=500, description="Optional message to include with the share"
    )

    @field_validator("recipient_ids")
    def validate_recipient_ids(cls, v):
        if not v:
            raise ValidationError("At least one recipient ID is required")
        if len(v) > 5:
            raise ValidationError("Cannot share to more than 5 users at once")
        if len(set(v)) != len(v):
            raise ValidationError("Duplicate recipient IDs are not allowed")
        return v

    @field_validator("message")
    def validate_message(cls, v):
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None

    class Config:
        json_schema_extra = {
            "example": {
                "tweet_id": 123,
                "recipient_ids": ["AB12345", "CD67890", "EF11111"],
                "message": "Check out this interesting tweet!",
            }
        }
