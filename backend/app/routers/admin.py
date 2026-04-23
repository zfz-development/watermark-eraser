from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.models.user import User
from sqlalchemy.orm import Session
from app.database import get_db
from sqlalchemy import func
from app.utils.response import success

router = APIRouter(prefix="/admin", tags=["管理后台"])

@router.get("/stats")
async def get_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_users = db.query(func.count(User.id)).scalar()
    return success({"total_users": total_users, "today_new_users": 0, "total_tasks": 0, "today_tasks": 0, "total_revenue": 0, "today_revenue": 0, "active_tasks": {"pending": 0, "processing": 0}})

@router.get("/config")
async def get_config(user: User = Depends(get_current_user)):
    return success({"free_register_points": 5, "sign_in_points": 1, "sign_in_7_bonus": 3, "sign_in_30_bonus": 10, "invite_points": 3, "ad_reward_points": 2, "ad_daily_limit": 5, "file_expire_hours": 24, "max_files_per_user": 20, "points_cost": {"image_standard": 1, "image_hd": 3, "video_30s": 5, "video_3min": 15, "video_long": 30}})
