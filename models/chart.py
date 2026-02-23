from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .base import Base

class Chart(Base):
    __tablename__ = "charts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric = Column(String, nullable=False)
    time_range = Column(String, nullable=False)
    type = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
