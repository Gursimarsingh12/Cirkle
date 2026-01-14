from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime


class CommentResponse(BaseModel):
    id: int
    tweet_id: int
    user_id: str
    text: str
    parent_comment_id: Optional[int]
    like_count: int
    is_liked: bool
    created_at: datetime
    edited_at: Optional[datetime] = None
    user_name: Optional[str] = None
    photo: Optional[str] = None
    is_organizational: bool = False
    is_prime: bool = False


class TweetMediaResponse(BaseModel):
    media_type: Literal["image/jpeg", "image/png", "image/jpg", "image/webp"]
    media_path: Optional[str] = Field(None, description="Path to media file on server")


class TweetResponse(BaseModel):
    id: int
    user_id: str
    text: str
    media: List[TweetMediaResponse]
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    bookmark_count: int
    is_shared: bool
    is_liked: bool
    is_bookmarked: bool
    created_at: datetime
    edited_at: datetime | None
    user_name: Optional[str] = None
    photo: Optional[str] = None
    is_organizational: bool
    is_prime: bool
    comments: List[CommentResponse]
