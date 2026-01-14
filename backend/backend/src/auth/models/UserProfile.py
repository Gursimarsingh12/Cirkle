from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, LargeBinary
from sqlalchemy.orm import relationship
from database.base import Base, TimestampMixin


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"
    user_id = Column(
        String(7), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    name = Column(String(100), nullable=False)
    photo_path = Column(String(255), nullable=True)
    photo_content_type = Column(String(50), nullable=True)
    banner_path = Column(String(255), nullable=True)
    banner_content_type = Column(String(50), nullable=True)
    bio = Column(String(150))
    is_organizational = Column(Boolean, default=False, nullable=False)
    is_prime = Column(Boolean, default=False, nullable=False)
    command_id = Column(
        Integer, ForeignKey("commands.id", ondelete="CASCADE"), nullable=True
    )
    user = relationship("User", back_populates="profile")
    command = relationship("Command", back_populates="profiles")
