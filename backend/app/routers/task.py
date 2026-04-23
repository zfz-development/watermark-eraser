from fastapi import Body, APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
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

class RemoveWatermarkRequest(BaseModel):
    file_id: str
    mask: Optional[str] = None
    quality: str = "standard"

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    content = await file.read()
    ext = get_file_ext(file.filename or "")
    if ext in ALLOWED_IMAGES:
        file_type = "image"
        if len(content) > MAX_IMAGE_SIZE:
            return error(1003, "图片大小超30MB")
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
async def remove_watermark(req: dict = Body(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    import json
    file_id = req.get('file_id', '')
    mask = req.get('mask', None)
    quality = req.get('quality', 'standard')
    mask_data = None
    if mask:
        try:
            mask_data = json.loads(mask)
            if isinstance(mask_data, str):
                mask_data = json.loads(mask_data)
        except: pass
    file_path = get_file_path(file_id)
    if not file_path or not os.path.exists(file_path):
        return error(1004, "file not found")
    ext = get_file_ext(file_path)
    file_type = "image" if ext in ALLOWED_IMAGES else "video" if ext in ALLOWED_VIDEOS else None
    if not file_type:
        return error(1002, "invalid format")
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
    ok, remaining = deduct_points(db, user.id, cost, "watermark")
    if not ok:
        return error(1005, f"insufficient points: {remaining}")
    task = Task(user_id=user.id, file_type=file_type, status="processing", input_url=file_id, cost_points=cost, input_size=os.path.getsize(file_path))
    db.add(task)
    db.commit()
    db.refresh(task)
    import asyncio
    from app.services.watermark.factory import get_engine
    async def do_process():
        try:
            engine = get_engine()
            out_ext = ".png" if file_type == "image" else ".mp4"
            out_id = generate_file_id() + out_ext
            out_path = os.path.join(os.path.dirname(file_path), out_id)
            if file_type == "image":
                result = await engine.remove_image(file_path, out_path, mask=mask_data)
            else:
                result = await engine.remove_video(file_path, out_path, mask=mask_data)
            if result.get("success"):
                task.status = "done"
                task.output_url = out_id
            else:
                task.status = "failed"
                task.error_msg = result.get("error", "process failed")
                from app.services.point_service import add_points
                add_points(db, user.id, cost, "refund")
        except Exception as ex:
            task.status = "failed"
            task.error_msg = str(ex)
            from app.services.point_service import add_points
            add_points(db, user.id, cost, "refund")
        finally:
            db.commit()
    asyncio.create_task(do_process())
    return success({"task_id": task.id, "status": "processing", "cost_points": cost, "remaining_points": user.points, "estimated_time": 10 if file_type == "image" else 30})

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
