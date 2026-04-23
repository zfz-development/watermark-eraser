import os
base = r'C:\Users\Administrator\.openclaw\workspace\watermark-eraser\backend'
def w(rel, content):
    p = os.path.join(base, rel)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)

w('app/routers/task.py', '''from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.task import Task
from app.services.point_service import deduct_points
from app.utils.response import success, error
from app.utils.file import generate_file_id, get_file_ext, save_upload_file, get_file_path, ALLOWED_IMAGES, ALLOWED_VIDEOS, MAX_IMAGE_SIZE, MAX_VIDEO_SIZE
from PIL import Image
from datetime import datetime, timedelta
import os

router = APIRouter(tags=["核心业务"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    content = await file.read()
    ext = get_file_ext(file.filename or "")
    if ext in ALLOWED_IMAGES:
        file_type = "image"
        if len(content) > MAX_IMAGE_SIZE:
            return error(1003, "图片大小超过30MB")
    elif ext in ALLOWED_VIDEOS:
        file_type = "video"
        if len(content) > MAX_VIDEO_SIZE:
            return error(1003, "视频大小超过500MB")
    else:
        return error(1002, "不支持的文件格式")
    file_id = generate_file_id()
    save_path = save_upload_file(content, file.filename or f"{file_id}.{ext}", file_id)
    width, height, duration = None, None, None
    if file_type == "image":
        try:
            img = Image.open(save_path)
            width, height = img.size
        except: pass
    elif file_type == "video":
        try:
            import subprocess, json
            r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", save_path], capture_output=True, text=True, timeout=10)
            info = json.loads(r.stdout)
            duration = float(info.get("format", {}).get("duration", 0))
        except: pass
    expires_at = datetime.utcnow() + timedelta(hours=24)
    return success({"file_id": file_id, "file_type": file_type, "file_name": file.filename, "file_size": len(content), "width": width, "height": height, "duration": duration, "preview_url": f"/api/v1/download/{file_id}", "expires_at": expires_at.isoformat()})

@router.post("/watermark/remove")
async def remove_watermark(file_id: str, mask: str = None, quality: str = "standard", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    import json
    mask_list = None
    if mask:
        try: mask_list = json.loads(mask)
        except: pass
    file_path = get_file_path(file_id)
    if not file_path or not os.path.exists(file_path):
        return error(1004, "文件不存在")
    ext = get_file_ext(file_path)
    file_type = "image" if ext in ALLOWED_IMAGES else "video" if ext in ALLOWED_VIDEOS else None
    if not file_type:
        return error(1002, "文件格式错误")
    cost = 1
    if file_type == "image":
        cost = 1 if quality == "standard" else 3
    else:
        try:
            import subprocess, json as j
            r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", file_path], capture_output=True, text=True, timeout=10)
            dur = float(j.loads(r.stdout).get("format", {}).get("duration", 0))
            cost = 5 if dur <= 30 else 15 if dur <= 180 else 30
        except: cost = 5
    ok, remaining = deduct_points(db, user.id, cost, "去水印")
    if not ok:
        return error(1005, f"积分不足，当前{remaining}积分")
    task = Task(user_id=user.id, file_type=file_type, status="pending_config", input_url=file_id, cost_points=cost, input_size=os.path.getsize(file_path))
    db.add(task)
    db.commit()
    db.refresh(task)
    return success({"task_id": task.id, "status": "pending_config", "cost_points": cost, "remaining_points": user.points, "estimated_time": 10 if file_type == "image" else 30})

@router.get("/task/{task_id}")
async def get_task(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        return error(1004, "任务不存在")
    return success({"task_id": task.id, "status": task.status, "file_type": task.file_type, "input_preview_url": f"/api/v1/download/{task.input_url}" if task.input_url else None, "output_url": f"/api/v1/download/{task.output_url}" if task.output_url else None, "cost_points": task.cost_points, "error_msg": task.error_msg, "created_at": task.created_at.isoformat() if task.created_at else None, "finished_at": task.finished_at.isoformat() if task.finished_at else None})

@router.get("/tasks")
async def get_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db), page: int = 1, page_size: int = 20, status: str = None, file_type: str = None):
    query = db.query(Task).filter(Task.user_id == user.id)
    if status:
        query = query.filter(Task.status == status)
    if file_type:
        query = query.filter(Task.file_type == file_type)
    total = query.count()
    tasks = query.order_by(Task.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    items = [{"task_id": t.id, "status": t.status, "file_type": t.file_type, "input_preview_url": f"/api/v1/download/{t.input_url}" if t.input_url else None, "output_url": f"/api/v1/download/{t.output_url}" if t.output_url else None, "cost_points": t.cost_points, "error_msg": t.error_msg, "created_at": t.created_at.isoformat() if t.created_at else None, "finished_at": t.finished_at.isoformat() if t.finished_at else None} for t in tasks]
    return success({"total": total, "page": page, "page_size": page_size, "items": items})

@router.delete("/task/{task_id}")
async def delete_task(task_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.user_id == user.id).first()
    if not task:
        return error(1004, "任务不存在")
    db.delete(task)
    db.commit()
    return success(message="删除成功")

@router.get("/download/{file_id}")
async def download_file(file_id: str, user: User = Depends(get_current_user)):
    file_path = get_file_path(file_id)
    if not file_path or not os.path.exists(file_path):
        return error(1004, "文件不存在")
    return FileResponse(file_path, filename=os.path.basename(file_path))
''')

w('app/routers/shop.py', '''from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.models.user import User
from app.utils.response import success, error
from datetime import datetime

router = APIRouter(prefix="/shop", tags=["商城"])

PACKAGES = [
    {"id": 1, "name": "体验包", "points": 30, "price": 6.00, "original_price": None, "badge": None, "popular": False},
    {"id": 2, "name": "标准包", "points": 100, "price": 15.00, "original_price": 20.00, "badge": "推荐", "popular": True},
    {"id": 3, "name": "专业包", "points": 500, "price": 50.00, "original_price": None, "badge": None, "popular": False},
    {"id": 4, "name": "尊享包", "points": 2000, "price": 150.00, "original_price": 200.00, "badge": "最划算", "popular": False},
]

VIP_PLANS = [
    {"id": 1, "level": 1, "name": "基础VIP", "duration": 1, "duration_unit": "month", "price": 19.00, "original_price": None, "image_quota": 200, "video_quota": 20, "features": ["200次图片去水印", "20次视频去水印", "高优先级处理"], "badge": None},
    {"id": 2, "level": 2, "name": "专业VIP", "duration": 1, "duration_unit": "month", "price": 39.00, "original_price": None, "image_quota": 1000, "video_quota": 100, "features": ["1000次图片去水印", "100次视频去水印", "批量处理", "API访问"], "badge": None},
    {"id": 3, "level": 2, "name": "年费VIP", "duration": 12, "duration_unit": "month", "price": 199.00, "original_price": 468.00, "image_quota": -1, "video_quota": 500, "features": ["不限图片去水印", "500次视频/月", "所有功能", "专属客服"], "badge": "省269元"},
]

@router.get("/packages")
async def get_packages():
    return success(PACKAGES)

@router.get("/vip-plans")
async def get_vip_plans():
    return success(VIP_PLANS)

@router.post("/order/points")
async def create_point_order(package_id: int, user: User = Depends(get_current_user)):
    pkg = next((p for p in PACKAGES if p["id"] == package_id), None)
    if not pkg:
        return error(1001, "套餐不存在")
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{user.id}"
    return success({"order_id": order_id, "points": pkg["points"], "amount": pkg["price"], "pay_status": "pending", "pay_methods": ["wechat", "alipay"], "created_at": datetime.utcnow().isoformat()})

@router.post("/order/vip")
async def create_vip_order(plan_id: int, user: User = Depends(get_current_user)):
    plan = next((p for p in VIP_PLANS if p["id"] == plan_id), None)
    if not plan:
        return error(1001, "套餐不存在")
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{user.id}"
    return success({"order_id": order_id, "points": None, "amount": plan["price"], "pay_status": "pending", "pay_methods": ["wechat", "alipay"], "created_at": datetime.utcnow().isoformat()})

@router.post("/order/callback")
async def payment_callback():
    return error(1011, "功能配置中")
''')

w('app/routers/admin.py', '''from fastapi import APIRouter, Depends
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
''')

print('part5 done')
