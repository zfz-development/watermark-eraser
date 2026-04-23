from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base

class PointLog(Base):
    __tablename__ = "point_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    type = Column(String(30), nullable=False)
    detail = Column(String(255), nullable=True)
    task_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class SignInLog(Base):
    __tablename__ = "sign_in_logs"
    __table_args__ = (UniqueConstraint("user_id", "date"),)
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    reward = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
