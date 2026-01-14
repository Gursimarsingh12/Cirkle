from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from database.base import Base, TimestampMixin

class Token(Base, TimestampMixin):
    __tablename__ = "tokens"
    user_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    user = relationship("User", back_populates="tokens")
    __table_args__ = (
        Index("idx_token_expires_at", "expires_at"),
        Index("idx_access_token_hash", "access_token"),
    )