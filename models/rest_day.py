from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from .base import Base

class RestDay(Base):
    __tablename__ = "rest_days"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_id = Column(String, nullable=True)
    user_sync_token = Column(String, ForeignKey("user_profile.sync_token"), nullable=False)
    date = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
