from database.base import Base, TimestampMixin
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship


class Share(Base, TimestampMixin):
    __tablename__ = "shares"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    tweet_id = Column(
        Integer, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False
    )
    recipient_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    message = Column(String(500), nullable=True)
    shared_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    
    tweet = relationship("Tweet", back_populates="shares")
    sender = relationship("User", foreign_keys=[user_id], back_populates="sent_shares")
    recipient = relationship(
        "User", foreign_keys=[recipient_id], back_populates="received_shares"
    )
