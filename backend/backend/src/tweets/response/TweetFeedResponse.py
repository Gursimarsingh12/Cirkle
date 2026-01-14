from pydantic import BaseModel
from typing import List, Optional
from .TweetResponse import TweetResponse


class TweetFeedResponse(BaseModel):
    tweets: List[TweetResponse]
    total: int
    page: int
    page_size: int
    has_more: Optional[bool] = None
    feed_type: Optional[str] = "latest"
    last_tweet_id: Optional[int] = None
    refresh_timestamp: Optional[str] = None
