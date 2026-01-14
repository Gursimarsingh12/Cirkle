from database.base import Base, TimestampMixin
from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint, LargeBinary
from sqlalchemy.orm import relationship


class TweetMedia(Base, TimestampMixin):
    __tablename__ = "tweet_media"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tweet_id = Column(
        Integer, ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False
    )
    media_type = Column(String(50), nullable=True)
    media_path = Column(String(255), nullable=True)
    __table_args__ = (
        CheckConstraint(
            "media_type IN ('image/jpeg', 'image/png', 'image/jpg', 'image/webp')",
            name="check_media_type_is_image",
        ),
    )
    tweet = relationship("Tweet", back_populates="media")
