import os
base = r'C:\Users\Administrator\.openclaw\workspace\watermark-eraser\backend'
def w(rel, content):
    p = os.path.join(base, rel)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)

w('app/routers/user.py', '''from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.auth import create_token
from app.services.point_service import add_points, get_today_sign_in
from app.utils.response import success, error
from app.config import settings
import random, string

router = APIRouter(prefix="/user", tags=["用户"])

@router.post("/sms/send")
async def send_sms(phone: str):
    return success(message="验证码已发送")

@router.post("/register")
async def register(phone: str, code: str, invite_code: str = None, db: Session = Depends(get_db)):
    if code != settings.SMS_VERIFY_CODE:
        return error(1007, "验证码错误")
    existing = db.query(User).filter(User.phone == phone).first()
    if existing:
        return error(1006, "手机号已注册")
    user = User(
        phone=phone,
        nickname=f"用户_{phone[-4:]}",
        points=5,
        invite_code=''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    )
    if invite_code:
        inviter = db.query(User).filter(User.invite_code == invite_code).first()
        if inviter:
            user.invited_by = inviter.id
            db.add(user)
            db.commit()
            db.refresh(user)
            add_points(db, inviter.id, 3, "invite_received", f"邀请用户注册")
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
async def login(phone: str, code: str, db: Session = Depends(get_db)):
    if code != settings.SMS_VERIFY_CODE:
        return error(1007, "验证码错误")
    user = db.query(User).filter(User.phone == phone).first()
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
async def update_profile(nickname: str = None, avatar_url: str = None, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if nickname is not None:
        user.nickname = nickname
    if avatar_url is not None:
        user.avatar_url = avatar_url
    db.commit()
    return success(message="更新成功")

@router.post("/refresh-token")
async def refresh_token(user: User = Depends(get_current_user)):
    token = create_token(user.id)
    return success({"token": token})
''')

w('app/routers/points.py', '''from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.point import SignInLog
from app.services.point_service import add_points, get_consecutive_days, get_today_sign_in, get_points_logs
from app.utils.response import success, error
from datetime import date

router = APIRouter(prefix="/user", tags=["积分"])

@router.post("/sign-in")
async def sign_in(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if get_today_sign_in(db, user.id):
        return error(1001, "今日已签到")
    days = get_consecutive_days(db, user.id)
    reward = 1
    detail = "每日签到"
    if days + 1 == 7:
        reward = 4
        detail = "每日签到(连续7天额外+3)"
    elif days + 1 == 30:
        reward = 11
        detail = "每日签到(连续30天额外+10)"
    log = SignInLog(user_id=user.id, date=date.today(), reward=reward)
    db.add(log)
    total = add_points(db, user.id, reward, "sign_in", detail)
    new_days = get_consecutive_days(db, user.id)
    return success({"reward_points": reward, "total_points": total, "consecutive_days": new_days})

@router.post("/invite")
async def invite(invite_code: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if invite_code == user.invite_code:
        return error(1001, "不能邀请自己")
    total = add_points(db, user.id, 3, "invite", "邀请好友奖励")
    return success({"reward_points": 3, "total_points": total})

@router.get("/points")
async def get_points(user: User = Depends(get_current_user)):
    return success(user.points)

@router.get("/points/logs")
async def get_point_logs(user: User = Depends(get_current_user), db: Session = Depends(get_db), page: int = 1, page_size: int = 20):
    result = get_points_logs(db, user.id, page, page_size)
    items = [{"id": i.id, "amount": i.amount, "type": i.type, "detail": i.detail, "task_id": i.task_id, "created_at": i.created_at.isoformat() if i.created_at else None} for i in result["items"]]
    result["items"] = items
    return success(result)

@router.post("/ad-reward")
async def ad_reward():
    return error(1011, "功能配置中")
''')

print('part4 done')
