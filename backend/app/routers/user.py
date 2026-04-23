from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.auth import create_token
from app.services.point_service import add_points, get_today_sign_in
from app.utils.response import success, error
from app.config import settings
import random, string

router = APIRouter(prefix="/user", tags=["用户"])

class SendSmsRequest(BaseModel):
    phone: str

class RegisterRequest(BaseModel):
    phone: str
    code: str
    invite_code: Optional[str] = None

class LoginRequest(BaseModel):
    phone: str
    code: str

class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

@router.post("/sms/send")
async def send_sms(req: SendSmsRequest):
    return success(message="验证码已发送")

@router.post("/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if req.code != settings.SMS_VERIFY_CODE:
        return error(1007, "验证码错误")
    existing = db.query(User).filter(User.phone == req.phone).first()
    if existing:
        return error(1006, "手机号已注册")
    user = User(
        phone=req.phone,
        nickname=f"用户_{req.phone[-4:]}",
        points=5,
        invite_code="".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    )
    if req.invite_code:
        inviter = db.query(User).filter(User.invite_code == req.invite_code).first()
        if inviter:
            user.invited_by = inviter.id
            db.add(user)
            db.commit()
            db.refresh(user)
            add_points(db, inviter.id, 3, "invite_received", "邀请用户注册")
            add_points(db, user.id, 3, "invite", "填写邀请码奖励")
            db.refresh(user)
        else:
            db.add(user)
            db.commit()
            db.refresh(user)
    else:
        db.add(user)
        db.commit()
        db.refresh(user)
    add_points(db, user.id, 5, "register", "新用户注册奖励")
    db.refresh(user)
    token = create_token(user.id)
    return success({
        "token": token,
        "user": {
            "id": user.id,
            "phone": f"{user.phone[:3]}****{user.phone[7:]}",
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "points": user.points,
            "vip_level": user.vip_level,
            "vip_expire_at": user.vip_expire_at.isoformat() if user.vip_expire_at else None,
            "invite_code": user.invite_code,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    })

@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    if req.code != settings.SMS_VERIFY_CODE:
        return error(1007, "验证码错误")
    user = db.query(User).filter(User.phone == req.phone).first()
    if not user:
        return error(1007, "用户不存在")
    token = create_token(user.id)
    return success({
        "token": token,
        "user": {
            "id": user.id,
            "phone": f"{user.phone[:3]}****{user.phone[7:]}",
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "points": user.points,
            "vip_level": user.vip_level,
            "vip_expire_at": user.vip_expire_at.isoformat() if user.vip_expire_at else None,
            "invite_code": user.invite_code,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    })

@router.post("/wechat-login")
async def wechat_login():
    return error(1011, "功能配置中")

@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return success({
        "id": user.id,
        "phone": f"{user.phone[:3]}****{user.phone[7:]}" if user.phone else None,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "points": user.points,
        "vip_level": user.vip_level,
        "vip_expire_at": user.vip_expire_at.isoformat() if user.vip_expire_at else None,
        "invite_code": user.invite_code,
        "total_used": user.total_used,
        "today_sign_in": get_today_sign_in(db, user.id),
        "created_at": user.created_at.isoformat() if user.created_at else None
    })

@router.put("/profile")
async def update_profile(req: UpdateProfileRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.nickname is not None:
        user.nickname = req.nickname
    if req.avatar_url is not None:
        user.avatar_url = req.avatar_url
    db.commit()
    return success(message="更新成功")

@router.post("/refresh-token")
async def refresh_token(user: User = Depends(get_current_user)):
    token = create_token(user.id)
    return success({"token": token})
