from database.base import Base, TimestampMixin
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


class CommentLike(Base, TimestampMixin):
    __tablename__ = "comment_likes"
    user_id = Column(
        String(7),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    comment_id = Column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), primary_key=True
    )
    comment = relationship("Comment", back_populates="likes")
    user = relationship("User", back_populates="comment_likes")
