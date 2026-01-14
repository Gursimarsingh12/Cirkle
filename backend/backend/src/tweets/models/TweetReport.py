from database.base import Base, TimestampMixin
from sqlalchemy import JSON, Column, Integer, String, Text, ForeignKey
from typing import Dict, Any, Optional


class TweetReport(Base, TimestampMixin):
    __tablename__ = "tweet_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tweet_id = Column(
        Integer, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(String(7), nullable=False)
    reason = Column(Text)
    snapshot = Column(JSON, nullable=True)

    def __init__(
        self,
        tweet_id: int,
        user_id: str,
        reason: str,
        snapshot: Optional[Dict[str, Any]] = None,
    ):
        self.tweet_id = tweet_id
        self.user_id = user_id
        self.reason = reason
        self.snapshot = snapshot
