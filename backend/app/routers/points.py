from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.point import SignInLog
from app.services.point_service import add_points, get_consecutive_days, get_today_sign_in, get_points_logs
from app.utils.response import success, error
from datetime import date

router = APIRouter(prefix="/user", tags=["积分"])

class InviteRequest(BaseModel):
    invite_code: str

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
async def invite(req: InviteRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.invite_code == user.invite_code:
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
