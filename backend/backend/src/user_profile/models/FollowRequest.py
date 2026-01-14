from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Enum,
    DateTime,
    func,
    UniqueConstraint,
)
from database.base import Base
import enum


class FollowRequestStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class FollowRequest(Base):
    __tablename__ = "follow_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    follower_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    followee_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    status = Column(
        Enum(FollowRequestStatus), default=FollowRequestStatus.pending, nullable=False
    )
    created_at = Column(DateTime, default=func.current_timestamp(), nullable=False)
    __table_args__ = (
        UniqueConstraint("follower_id", "followee_id", name="uix_follower_followee"),
    )
