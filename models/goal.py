from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from .base import Base

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_profile_id = Column(Integer, ForeignKey("user_profile.id"), nullable=False)
    daily_skips = Column(Integer, nullable=True)
    weekly_skips = Column(Integer, nullable=True)
    weekly_workouts = Column(Integer, nullable=True)
    daily_calories = Column(Integer, nullable=True)
    weekly_calories = Column(Integer, nullable=True)
    weekly_duration = Column(Integer, nullable=True)
    skip_rate_goal = Column(Float, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
