from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class ReportResponse(BaseModel):
    id: int = Field(..., description="ID of the report")
    tweet_id: Optional[int] = Field(None, description="ID of the reported tweet")
    comment_id: Optional[int] = Field(None, description="ID of the reported comment")
    user_id: str = Field(..., description="ID of the reporting user")
    reason: str = Field(..., description="Reason for the report")
    snapshot: Optional[Dict[str, Any]] = Field(
        None, description="Snapshot of the reported content"
    )
    created_at: datetime = Field(..., description="When the report was created")
    updated_at: datetime = Field(..., description="When the report was last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "tweet_id": 123,
                "user_id": "u123456",
                "reason": "Inappropriate content",
                "snapshot": {
                    "id": 123,
                    "text": "Reported content",
                    "created_at": "2024-03-20T10:00:00Z",
                },
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z",
            }
        }
