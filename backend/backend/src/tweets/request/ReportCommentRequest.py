from pydantic import BaseModel, Field


class ReportCommentRequest(BaseModel):
    comment_id: int = Field(...)
    reason: str = Field(..., max_length=500)
