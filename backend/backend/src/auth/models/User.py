from sqlalchemy import Column, String, Date, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from database.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    user_id = Column(String(7), primary_key=True, nullable=False)
    password = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    is_private = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_online = Column(Boolean, default=False, nullable=False)
    command_id = Column(Integer, ForeignKey("commands.id", ondelete="CASCADE"), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    block_until = Column(Date, nullable=True)
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan",)
    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    command = relationship("Command", back_populates="users")
    followers = relationship("Follower", foreign_keys="Follower.followee_id", back_populates="followee")
    following = relationship("Follower", foreign_keys="Follower.follower_id", back_populates="follower")
    tweets = relationship("Tweet", back_populates="user")
    sent_shares = relationship("Share", foreign_keys="Share.user_id", back_populates="sender")
    received_shares = relationship("Share", foreign_keys="Share.recipient_id", back_populates="recipient")
    tweet_likes = relationship("TweetLike", back_populates="user")
    comment_likes = relationship("CommentLike", back_populates="user")
    bookmarks = relationship("Bookmark", back_populates="user")
