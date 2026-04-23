from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), unique=True, nullable=True)
    wechat_openid = Column(String(64), unique=True, nullable=True)
    nickname = Column(String(50), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    points = Column(Integer, default=0)
    vip_level = Column(Integer, default=0)
    vip_expire_at = Column(DateTime, nullable=True)
    invite_code = Column(String(8), unique=True, nullable=True)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    total_used = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
