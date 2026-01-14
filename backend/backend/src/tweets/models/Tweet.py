from database.base import Base, TimestampMixin
from sqlalchemy import JSON, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship


class Tweet(Base, TimestampMixin):
    __tablename__ = "tweets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    text = Column(Text(500), nullable=False)
    view_count = Column(Integer, default=0)
    edited_at = Column(DateTime, nullable=True)
    user = relationship("User", back_populates="tweets")
    likes = relationship("TweetLike", back_populates="tweet")
    comments = relationship("Comment", back_populates="tweet")
    bookmarks = relationship("Bookmark", back_populates="tweet")
    shares = relationship("Share", back_populates="tweet")
    media = relationship("TweetMedia", back_populates="tweet")
