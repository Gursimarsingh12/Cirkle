from database.base import Base, TimestampMixin
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class Bookmark(Base, TimestampMixin):
    __tablename__ = "bookmarks"
    user_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    tweet_id = Column(
        Integer, ForeignKey("tweets.id", ondelete="CASCADE"), primary_key=True
    )
    tweet = relationship("Tweet", back_populates="bookmarks")
    user = relationship("User", back_populates="bookmarks")
