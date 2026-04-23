from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.dependencies import get_current_user
from app.models.user import User
from app.utils.response import success, error
from datetime import datetime

router = APIRouter(prefix="/shop", tags=["商城"])

class PointOrderRequest(BaseModel):
    package_id: int

class VipOrderRequest(BaseModel):
    plan_id: int

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
async def create_point_order(req: PointOrderRequest, user: User = Depends(get_current_user)):
    pkg = next((p for p in PACKAGES if p["id"] == req.package_id), None)
    if not pkg:
        return error(1001, "套餐不存在")
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{user.id}"
    return success({"order_id": order_id, "points": pkg["points"], "amount": pkg["price"], "pay_status": "pending", "pay_methods": ["wechat", "alipay"], "created_at": datetime.utcnow().isoformat()})

@router.post("/order/vip")
async def create_vip_order(req: VipOrderRequest, user: User = Depends(get_current_user)):
    plan = next((p for p in VIP_PLANS if p["id"] == req.plan_id), None)
    if not plan:
        return error(1001, "套餐不存在")
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{user.id}"
    return success({"order_id": order_id, "points": None, "amount": plan["price"], "pay_status": "pending", "pay_methods": ["wechat", "alipay"], "created_at": datetime.utcnow().isoformat()})

@router.post("/order/callback")
async def payment_callback():
    return error(1011, "功能配置中")
