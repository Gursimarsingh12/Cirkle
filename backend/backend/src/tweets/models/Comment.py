from database.base import Base, TimestampMixin
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship


class Comment(Base, TimestampMixin):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tweet_id = Column(
        Integer, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    parent_comment_id = Column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    text = Column(Text, nullable=False)
    edited_at = Column(DateTime, nullable=True)
    tweet = relationship("Tweet", back_populates="comments")
    parent_comment = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent_comment")
    likes = relationship("CommentLike", back_populates="comment")
