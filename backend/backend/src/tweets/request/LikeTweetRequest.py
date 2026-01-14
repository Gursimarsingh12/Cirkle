from pydantic import BaseModel, Field


class LikeTweetRequest(BaseModel):
    tweet_id: int = Field(...)
    like: bool = Field(...)
