import os
base = r'C:\Users\Administrator\.openclaw\workspace\watermark-eraser\backend'

def w(rel, content):
    p = os.path.join(base, rel)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)

w('app/config.py', '''from pydantic_settings import BaseSettings
from pydantic import Field
import yaml
from pathlib import Path

class Settings(BaseSettings):
    SECRET_KEY: str = "dev-secret-key"
    DATABASE_URL: str = "sqlite:///./data.db"
    SMS_VERIFY_CODE: str = "888888"
    class Config:
        env_file = ".env"

settings = Settings()

def load_yaml_config():
    p = Path(__file__).parent.parent / "config.yaml"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}

yaml_config = load_yaml_config()
''')

w('app/database.py', '''from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine("sqlite:///./data.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
''')

w('app/dependencies.py', '''from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.config import settings
from app.database import get_db
from sqlalchemy.orm import Session
from app.models.user import User

security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token无效")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token已过期")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user
''')

w('app/utils/response.py', '''def success(data=None, message="success"):
    return {"code": 0, "message": message, "data": data}

def error(code, message):
    return {"code": code, "message": message, "data": None}
''')

w('app/utils/file.py', '''import os, uuid
from datetime import datetime
from pathlib import Path

UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_IMAGES = {"jpg", "jpeg", "png", "webp"}
ALLOWED_VIDEOS = {"mp4", "mov", "avi"}
MAX_IMAGE_SIZE = 30 * 1024 * 1024
MAX_VIDEO_SIZE = 500 * 1024 * 1024

def generate_file_id():
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = str(uuid.uuid4().int)[:6]
    return f"FILE{ts}{rand}"

def get_file_ext(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

def save_upload_file(file_data, filename, file_id):
    ext = get_file_ext(filename)
    save_name = f"{file_id}.{ext}"
    save_path = UPLOAD_DIR / save_name
    with open(save_path, "wb") as f:
        f.write(file_data)
    return str(save_path)

def get_file_path(file_id):
    for f in UPLOAD_DIR.iterdir():
        if f.name.startswith(file_id):
            return str(f)
    return ""
''')

w('app/services/auth.py', '''from datetime import datetime, timedelta
from jose import jwt
from app.config import settings

def create_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=7)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
''')

w('app/services/point_service.py', '''from sqlalchemy.orm import Session
from app.models.point import PointLog, SignInLog
from app.models.user import User
from datetime import date, timedelta

def add_points(db, user_id, amount, ptype, detail, task_id=None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return -1
    user.points += amount
    log = PointLog(user_id=user_id, amount=amount, type=ptype, detail=detail, task_id=task_id)
    db.add(log)
    db.commit()
    db.refresh(user)
    return user.points

def deduct_points(db, user_id, amount, detail, task_id=None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False, 0
    if user.points < amount:
        return False, user.points
    user.points -= amount
    log = PointLog(user_id=user_id, amount=-amount, type="use", detail=detail, task_id=task_id)
    db.add(log)
    db.commit()
    db.refresh(user)
    return True, user.points

def get_consecutive_days(db, user_id):
    days = 0
    check_date = date.today()
    while True:
        log = db.query(SignInLog).filter(SignInLog.user_id == user_id, SignInLog.date == check_date).first()
        if log:
            days += 1
            check_date -= timedelta(days=1)
        else:
            break
    return days

def get_today_sign_in(db, user_id):
    return db.query(SignInLog).filter(SignInLog.user_id == user_id, SignInLog.date == date.today()).first() is not None

def get_points_logs(db, user_id, page=1, page_size=20):
    query = db.query(PointLog).filter(PointLog.user_id == user_id).order_by(PointLog.id.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "page_size": page_size, "items": items}
''')

print('part2 done')
