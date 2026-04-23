from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_type = Column(String(10), nullable=False)
    engine = Column(String(30), default="placeholder")
    status = Column(String(20), default="pending")
    input_url = Column(String(500), nullable=True)
    output_url = Column(String(500), nullable=True)
    input_size = Column(Integer, nullable=True)
    cost_points = Column(Integer, default=0)
    error_msg = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)
