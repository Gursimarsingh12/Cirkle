from pydantic import BaseModel
from datetime import datetime


class TweetStatsResponse(BaseModel):
    date: datetime
    total_tweets: int
    total_likes: int
    total_comments: int
    total_shares: int
    total_bookmarks: int
    total_views: int
