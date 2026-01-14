from pydantic import BaseModel, Field, field_validator
from typing import Optional
from core.exceptions import ValidationError


class ReportTweetRequest(BaseModel):
    tweet_id: int = Field(..., description="ID of the tweet being reported")
    reason: str = Field(
        ..., max_length=500, description="Reason for reporting the tweet"
    )

    @field_validator("reason")
    def validate_reason(cls, v):
        if not v.strip():
            raise ValidationError("Reason cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "tweet_id": 123,
                "reason": "This tweet contains inappropriate content",
            }
        }
