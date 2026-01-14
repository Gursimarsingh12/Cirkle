from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from tweets.response.TweetResponse import TweetResponse

class SharedTweetResponse(BaseModel):
    id: int
    tweet_id: int
    sender_id: str
    sender_name: str
    sender_photo_path: Optional[str] = None
    recipient_id: str
    recipient_name: str
    recipient_photo_path: Optional[str] = None
    message: Optional[str] = None
    shared_at: datetime
    tweet: TweetResponse
    image_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "tweet_id": 123,
                "sender_id": "AB12345",
                "sender_name": "Aditya Kumar",
                "sender_photo_path": "/static/profiles/AB12345.jpg",
                "recipient_id": "CD67890",
                "recipient_name": "Lt Gen Ram Chandar Tiwari",
                "recipient_photo_path": "/static/profiles/CD67890.jpg",
                "message": "Check out this interesting tweet!",
                "shared_at": "2024-03-20T10:00:00Z",
                "tweet": {
                    "id": 123,
                    "text": "India – US Army-to-Army Staff Talks were held in #NewDelhi from 28–30 May 2025...",
                    "user_id": "CD67890",
                    "username": "ltgenram",
                    "name": "Lt Gen Ram Chandar Tiwari",
                    "created_at": "2024-03-20T09:00:00Z",
                    "like_count": 28000,
                    "comment_count": 230,
                    "is_liked": "False",
                    "is_bookmarked": "True",
                    "user_photo_path": "/static/profiles/CD67890.jpg",
                    "account_type": "pub"
                },
                "image_count": 4
            }
        } 