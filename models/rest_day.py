from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .base import Base

class RestDay(Base):
    __tablename__ = "rest_days"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
