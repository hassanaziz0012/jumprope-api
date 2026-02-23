from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from .base import Base

class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    image = Column(String, nullable=True)
    ai_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
