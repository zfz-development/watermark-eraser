import os
base = r'C:\Users\Administrator\.openclaw\workspace\watermark-eraser\backend'

def w(rel, content):
    p = os.path.join(base, rel)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)

# Models
w('app/models/user.py', '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
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
''')

w('app/models/task.py', '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
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
''')

w('app/models/order.py', '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
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
''')

w('app/models/point.py', '''from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, UniqueConstraint
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
''')

# Watermark engine
w('app/services/watermark/base.py', '''from abc import ABC, abstractmethod
from typing import Optional

class WatermarkRemover(ABC):
    @abstractmethod
    async def remove_image(self, input_path, output_path, mask=None):
        pass
    @abstractmethod
    async def remove_video(self, input_path, output_path, mask=None):
        pass
    @property
    @abstractmethod
    def provider_name(self):
        pass
    @property
    @abstractmethod
    def quota_remaining(self):
        pass
''')

w('app/services/watermark/placeholder.py', '''from app.services.watermark.base import WatermarkRemover

class PlaceholderRemover(WatermarkRemover):
    @property
    def provider_name(self):
        return "placeholder"
    @property
    def quota_remaining(self):
        return 0
    async def remove_image(self, input_path, output_path, mask=None):
        return {"success": False, "status": "pending_config"}
    async def remove_video(self, input_path, output_path, mask=None):
        return {"success": False, "status": "pending_config"}
''')

w('app/services/watermark/factory.py', '''from app.services.watermark.base import WatermarkRemover
from app.services.watermark.placeholder import PlaceholderRemover

_engines = {"placeholder": PlaceholderRemover}

def get_engine(name="placeholder") -> WatermarkRemover:
    cls = _engines.get(name)
    if cls is None:
        raise ValueError(f"Unknown engine: {name}")
    return cls()
''')

print('part3 done')
