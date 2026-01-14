from pydantic import BaseModel, Field


class BookmarkTweetRequest(BaseModel):
    tweet_id: int = Field(...)
    bookmark: bool = Field(...)
