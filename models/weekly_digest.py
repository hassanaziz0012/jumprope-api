from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .base import Base

class WeeklyDigest(Base):
    __tablename__ = "weekly_digest"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_sync_token = Column(String, index=True, nullable=False)
    digest = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
