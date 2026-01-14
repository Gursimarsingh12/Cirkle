from sqlalchemy import Column, Integer, String

from sqlalchemy.orm import relationship

from database.base import Base

class Command(Base):
    __tablename__ = "commands"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    users = relationship("User", back_populates="command")
    profiles = relationship("UserProfile", back_populates="command")