from sqlalchemy import Column, String, ForeignKey, DateTime, func, PrimaryKeyConstraint

from database.base import Base

from sqlalchemy.orm import relationship


class Follower(Base):

    __tablename__ = "followers"

    follower_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    followee_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)

    __table_args__ = (PrimaryKeyConstraint(follower_id, followee_id),)

    follower = relationship(
        "User", foreign_keys=[follower_id], back_populates="following"
    )

    followee = relationship(
        "User", foreign_keys=[followee_id], back_populates="followers"
    )
