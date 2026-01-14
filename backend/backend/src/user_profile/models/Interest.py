from sqlalchemy import Column, Integer, String
from database.base import Base


class Interest(Base):
    __tablename__ = "interests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
