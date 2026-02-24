from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from .base import Base

class Chart(Base):
    __tablename__ = "charts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_profile_id = Column(Integer, ForeignKey("user_profile.id"), nullable=False)
    metric = Column(String, nullable=False)
    time_range = Column(String, nullable=False)
    type = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
