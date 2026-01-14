from sqlalchemy import Column, String, Integer, ForeignKey, PrimaryKeyConstraint
from database.base import Base


class UserInterest(Base):
    __tablename__ = "user_interests"
    user_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    interest_id = Column(
        Integer, ForeignKey("interests.id", ondelete="CASCADE"), nullable=False
    )
    __table_args__ = (PrimaryKeyConstraint(user_id, interest_id),)
