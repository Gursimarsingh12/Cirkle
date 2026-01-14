from pydantic import BaseModel, Field


class LikeCommentRequest(BaseModel):
    comment_id: int = Field(...)
    like: bool = Field(...)
