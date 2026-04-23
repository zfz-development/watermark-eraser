from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.database import Base

class VipOrder(Base):
    __tablename__ = "vip_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    level = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    pay_method = Column(String(20), nullable=True)
    pay_status = Column(String(20), default="pending")
    trade_no = Column(String(64), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class PointOrder(Base):
    __tablename__ = "point_orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    points = Column(Integer, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    pay_method = Column(String(20), nullable=True)
    pay_status = Column(String(20), default="pending")
    trade_no = Column(String(64), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
