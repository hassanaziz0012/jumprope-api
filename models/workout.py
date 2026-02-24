from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from .base import Base

class Workout(Base):
    __tablename__ = "workout"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_profile_id = Column(Integer, ForeignKey("user_profile.id"), nullable=False)
    date = Column(DateTime, nullable=False, server_default=func.now())
    duration = Column(Integer, nullable=False)
    total_skips = Column(Integer, nullable=False)
    avg_skips_per_minute = Column(Float, nullable=True)
    trips = Column(Integer, nullable=False, default=0)
    calories = Column(Float, nullable=True)
    heart_rate_avg = Column(Integer, nullable=True)
    heart_rate_max = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
