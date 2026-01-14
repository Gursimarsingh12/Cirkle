from pydantic import BaseModel, Field
from typing import Optional


class CommentTweetRequest(BaseModel):
    tweet_id: int = Field(...)
    text: str = Field(..., max_length=280)
    parent_comment_id: Optional[int] = None
