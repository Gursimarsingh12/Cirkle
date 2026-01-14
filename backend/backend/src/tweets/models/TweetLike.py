from database.base import Base, TimestampMixin
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class TweetLike(Base, TimestampMixin):
    __tablename__ = "tweet_likes"
    user_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    tweet_id = Column(
        Integer, ForeignKey("tweets.id", ondelete="CASCADE"), primary_key=True
    )
    tweet = relationship("Tweet", back_populates="likes")
    user = relationship("User", back_populates="tweet_likes")
