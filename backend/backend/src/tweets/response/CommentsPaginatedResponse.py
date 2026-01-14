from typing import List
from pydantic import BaseModel, Field
from tweets.response.TweetResponse import CommentResponse


class CommentsPaginatedResponse(BaseModel):
    comments: List[CommentResponse] = Field(...)
    page: int = Field(...)
    page_size: int = Field(...)
    total: int = Field(...)