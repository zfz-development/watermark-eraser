# API 接口规范 v1.0

> 冻结日期: 2026-04-08
> 状态: FROZEN — 未经项目Owner确认不得修改
> 基础路径: /api/v1

---

## 通用规范

### 请求格式
- Content-Type: application/json（除上传接口外）
- 认证: Bearer Token (JWT)，放在 Header `Authorization: Bearer <token>`
- 所有需要认证的接口未携带 Token 返回 401

### 统一响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 错误码

| code | 含义 |
|------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 文件格式不支持 |
| 1003 | 文件大小超限 |
| 1004 | 任务不存在 |
| 1005 | 积分不足 |
| 1006 | 用户已存在 |
| 1007 | 手机号或验证码错误 |
| 1008 | Token 过期或无效 |
| 1009 | 权限不足 |
| 1010 | 请求过于频繁 |
| 1011 | 引擎配置中，请稍后再试 |
| 1012 | 去水印处理失败 |
| 2001 | 服务器内部错误 |

### 分页参数（GET 列表接口通用）

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| page | int | 1 | 页码 |
| page_size | int | 20 | 每页数量，最大100 |

### 分页响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": []
  }
}
```

---

## 一、用户系统

### 1.1 发送验证码

```
POST /api/v1/user/sms/send
```

**请求 Body:**
```json
{
  "phone": "13800138000"
}
```

**响应:**
```json
{
  "code": 0,
  "message": "验证码已发送",
  "data": null
}
```

**规则:**
- 同一手机号 60 秒内只能发送一次
- 每日最多 5 次

---

### 1.2 手机号注册

```
POST /api/v1/user/register
```

**请求 Body:**
```json
{
  "phone": "13800138000",
  "code": "123456",
  "invite_code": "AB3K9P"    // 可选，邀请人邀请码
}
```

**响应:**
```json
{
  "code": 0,
  "message": "注册成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 1,
      "phone": "138****8000",
      "nickname": "用户_8000",
      "avatar_url": null,
      "points": 5,
      "vip_level": 0,
      "vip_expire_at": null,
      "invite_code": "XY7M2K",
      "created_at": "2026-04-08T12:00:00Z"
    }
  }
}
```

**规则:**
- 注册成功自动赠送 5 积分
- 自动生成 6 位邀请码
- 有邀请码时双方各得 3 积分
- token 有效期 7 天

---

### 1.3 手机号登录

```
POST /api/v1/user/login
```

**请求 Body:**
```json
{
  "phone": "13800138000",
  "code": "123456"
}
```

**响应:** 同注册响应格式

---

### 1.4 微信小程序登录（预留）

```
POST /api/v1/user/wechat-login
```

**请求 Body:**
```json
{
  "code": "wx_login_code",
  "nickname": "微信用户",
  "avatar_url": "https://..."
}
```

**响应:** 同注册响应格式

**当前行为:** 返回 `{"code": 1011, "message": "功能配置中", "data": null}`

---

### 1.5 获取用户信息

```
GET /api/v1/user/profile
```

**需要认证:** ✅

**响应:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "phone": "138****8000",
    "nickname": "用户_8000",
    "avatar_url": null,
    "points": 12,
    "vip_level": 0,
    "vip_expire_at": null,
    "invite_code": "XY7M2K",
    "total_used": 8,
    "today_sign_in": false,
    "created_at": "2026-04-08T12:00:00Z"
  }
}
```

---

### 1.6 更新用户信息

```
PUT /api/v1/user/profile
```

**需要认证:** ✅

**请求 Body:**
```json
{
  "nickname": "新昵称",     // 可选
  "avatar_url": "https://..."  // 可选
}
```

**响应:**
```json
{
  "code": 0,
  "message": "更新成功",
  "data": null
}
```

---

## 二、积分系统

### 2.1 每日签到

```
POST /api/v1/user/sign-in
```

**需要认证:** ✅

**响应:**
```json
{
  "code": 0,
  "message": "签到成功，获得1积分",
  "data": {
    "reward_points": 1,
    "total_points": 13,
    "consecutive_days": 3
  }
}
```

**规则:**
- 每日只能签到一次
- 连续签到 7 天额外奖励 3 积分
- 连续签到 30 天额外奖励 10 积分

---

### 2.2 邀请好友

```
POST /api/v1/user/invite
```

**需要认证:** ✅

**请求 Body:**
```json
{
  "invite_code": "AB3K9P"
}
```

**响应:**
```json
{
  "code": 0,
  "message": "邀请成功",
  "data": {
    "reward_points": 3,
    "total_points": 16
  }
}
```

**规则:**
- 不能邀请自己
- 同一邀请关系只能绑定一次

---

### 2.3 查看积分明细

```
GET /api/v1/user/points/logs?page=1&page_size=20
```

**需要认证:** ✅

**响应:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 25,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "amount": 5,
        "type": "register",
        "detail": "新用户注册奖励",
        "created_at": "2026-04-08T12:00:00Z"
      },
      {
        "id": 2,
        "amount": -1,
        "type": "use",
        "detail": "图片去水印",
        "task_id": 1,
        "created_at": "2026-04-08T12:05:00Z"
      },
      {
        "id": 3,
        "amount": 1,
        "type": "sign_in",
        "detail": "每日签到",
        "created_at": "2026-04-09T08:00:00Z"
      }
    ]
  }
}
```

**type 枚举:** register | sign_in | invite | invite_received | ad | purchase | use | refund | vip_reward

---

### 2.4 广告奖励（预留）

```
POST /api/v1/user/ad-reward
```

**需要认证:** ✅

**请求 Body:**
```json
{
  "ad_platform": "wechat",    // wechat | union_ads
  "ad_token": "xxx"           // 广告平台回执，用于验证
}
```

**当前行为:** 返回 `{"code": 1011, "message": "功能配置中", "data": null}`

**上线后响应:**
```json
{
  "code": 0,
  "message": "奖励已发放",
  "data": {
    "reward_points": 2,
    "total_points": 18,
    "today_ad_count": 2,
    "today_ad_limit": 5
  }
}
```

---

## 三、商城

### 3.1 积分包列表

```
GET /api/v1/shop/packages
```

**需要认证:** ❌（但认证后显示是否有优惠）

**响应:**
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "体验包",
      "points": 30,
      "price": 6.00,
      "original_price": null,
      "badge": null,
      "popular": false
    },
    {
      "id": 2,
      "name": "标准包",
      "points": 100,
      "price": 15.00,
      "original_price": 20.00,
      "badge": "推荐",
      "popular": true
    },
    {
      "id": 3,
      "name": "专业包",
      "points": 500,
      "price": 50.00,
      "original_price": null,
      "badge": null,
      "popular": false
    },
    {
      "id": 4,
      "name": "尊享包",
      "points": 2000,
      "price": 150.00,
      "original_price": 200.00,
      "badge": "最划算",
      "popular": false
    }
  ]
}
```

---

### 3.2 VIP 套餐列表

```
GET /api/v1/shop/vip-plans
```

**需要认证:** ❌

**响应:**
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "level": 1,
      "name": "基础VIP",
      "duration": 1,
      "duration_unit": "month",
      "price": 19.00,
      "image_quota": 200,
      "video_quota": 20,
      "features": ["200次图片去水印", "20次视频去水印", "高优先级处理"]
    },
    {
      "id": 2,
      "level": 2,
      "name": "专业VIP",
      "duration": 1,
      "duration_unit": "month",
      "price": 39.00,
      "image_quota": 1000,
      "video_quota": 100,
      "features": ["1000次图片去水印", "100次视频去水印", "批量处理", "API访问"]
    },
    {
      "id": 3,
      "level": 2,
      "name": "年费VIP",
      "duration": 12,
      "duration_unit": "month",
      "price": 199.00,
      "original_price": 468.00,
      "image_quota": -1,
      "video_quota": 500,
      "features": ["不限图片去水印", "500次视频/月", "所有功能", "专属客服"],
      "badge": "省¥269"
    }
  ]
}
```

> image_quota: -1 表示不限

---

### 3.3 创建积分购买订单

```
POST /api/v1/shop/order/points
```

**需要认证:** ✅

**请求 Body:**
```json
{
  "package_id": 2
}
```

**响应:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "order_id": "ORD20260408120001",
    "points": 100,
    "amount": 15.00,
    "pay_status": "pending",
    "pay_methods": ["wechat", "alipay"],
    "created_at": "2026-04-08T12:00:00Z"
  }
}
```

---

### 3.4 创建 VIP 购买订单

```
POST /api/v1/shop/order/vip
```

**需要认证:** ✅

**请求 Body:**
```json
{
  "plan_id": 2
}
```

**响应:** 同积分订单格式

---

### 3.5 支付回调（预留）

```
POST /api/v1/shop/order/callback
```

**说明:** 微信/支付宝支付成功后的异步回调通知，由支付平台调用，非前端调用。

**当前行为:** 返回 `{"code": 1011, "message": "功能配置中", "data": null}`

---

## 四、核心业务

### 4.1 上传文件

```
POST /api/v1/upload
```

**需要认证:** ✅

**Content-Type:** multipart/form-data

**参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | ✅ | 图片或视频文件 |

**文件限制:**
- 图片: jpg/png/webp, 最大 30MB
- 视频: mp4/mov/avi, 最大 500MB, 最长 10 分钟

**响应:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "file_id": "FILE20260408120001",
    "file_type": "image",      // image | video
    "file_name": "screenshot.png",
    "file_size": 2048576,
    "width": 1920,             // 图片有，视频无
    "height": 1080,
    "duration": null,          // 视频有(秒)，图片无
    "preview_url": "/api/v1/download/FILE20260408120001",
    "expires_at": "2026-04-09T12:00:00Z"
  }
}
```

**规则:**
- 上传的文件 24 小时后自动清理（除非关联了任务）
- 同一用户最多同时保留 20 个文件

---

### 4.2 提交去水印任务

```
POST /api/v1/watermark/remove
```

**需要认证:** ✅

**请求 Body:**
```json
{
  "file_id": "FILE20260408120001",
  "mask": [[100, 200, 300, 250]],   // 可选，手动框选水印区域 [x1, y1, x2, y2]
  "quality": "standard"              // standard | hd，仅图片有效
}
```

**响应:**
```json
{
  "code": 0,
  "message": "任务已提交",
  "data": {
    "task_id": 1,
    "status": "pending",
    "cost_points": 1,
    "remaining_points": 4,
    "estimated_time": 10
  }
}
```

**积分消耗计算:**

| 条件 | 消耗 |
|------|------|
| 图片 standard | 1 |
| 图片 hd | 3 |
| 视频 ≤30秒 | 5 |
| 视频 ≤3分钟 | 15 |
| 视频 >3分钟 | 30 |

**VIP 覆盖规则:**
- VIP 有效期内，扣除 VIP 额度而非积分
- VIP 额度不足时回退到积分

**estimated_time:** 预计秒数，图片约 5-10 秒，视频按长度计算

---

### 4.3 查询任务状态

```
GET /api/v1/task/{task_id}
```

**需要认证:** ✅

**响应:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": 1,
    "status": "done",         // pending | processing | done | failed | pending_config
    "file_type": "image",
    "input_preview_url": "/api/v1/download/FILE20260408120001",
    "output_url": "/api/v1/download/TASK20260408120001",
    "cost_points": 1,
    "error_msg": null,
    "created_at": "2026-04-08T12:00:00Z",
    "finished_at": "2026-04-08T12:00:08Z"
  }
}
```

**status 说明:**
- `pending`: 排队中
- `processing`: 处理中
- `done`: 完成，可下载
- `failed`: 失败，查看 error_msg，积分已退回
- `pending_config`: 引擎未配置

---

### 4.4 任务列表

```
GET /api/v1/tasks?page=1&page_size=20&status=done
```

**需要认证:** ✅

**查询参数:**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 默认 1 |
| page_size | int | 否 | 默认 20 |
| status | string | 否 | 筛选状态 |
| file_type | string | 否 | image | video |

**响应:** 分页格式，items 结构同 4.3

---

### 4.5 删除任务

```
DELETE /api/v1/task/{task_id}
```

**需要认证:** ✅

**响应:**
```json
{
  "code": 0,
  "message": "删除成功",
  "data": null
}
```

**规则:**
- 只能删除自己的任务
- 删除后释放文件存储空间
- 不退回积分

---

### 4.6 下载结果

```
GET /api/v1/download/{file_id}
```

**需要认证:** ✅

**响应:** 文件流（二进制），带 Content-Disposition header

**规则:**
- 只能下载自己的文件
- file_id 可以是上传文件 ID 或任务输出 ID
- 下载有频率限制：1 次/秒

---

## 五、管理后台（预留）

### 5.1 统计数据

```
GET /api/v1/admin/stats
```

**需要认证:** ✅（管理员）

**响应:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_users": 1234,
    "today_new_users": 56,
    "total_tasks": 5678,
    "today_tasks": 234,
    "total_revenue": 12345.67,
    "today_revenue": 678.90,
    "active_tasks": {
      "pending": 12,
      "processing": 5
    }
  }
}
```

---

### 5.2 用户列表

```
GET /api/v1/admin/users?page=1&page_size=20&keyword=xxx
```

**需要认证:** ✅（管理员）

---

### 5.3 系统配置

```
GET    /api/v1/admin/config
POST   /api/v1/admin/config
```

**需要认证:** ✅（管理员）

**配置项:**
```json
{
  "free_register_points": 5,
  "sign_in_points": 1,
  "sign_in_7_bonus": 3,
  "sign_in_30_bonus": 10,
  "invite_points": 3,
  "ad_reward_points": 2,
  "ad_daily_limit": 5,
  "file_expire_hours": 24,
  "max_files_per_user": 20,
  "points_cost": {
    "image_standard": 1,
    "image_hd": 3,
    "video_30s": 5,
    "video_3min": 15,
    "video_long": 30
  }
}
```

---

## 六、Token 刷新

```
POST /api/v1/user/refresh-token
```

**需要认证:** ✅

**响应:**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

---

*文档版本: v1.0 | 冻结日期: 2026-04-08 | 未经项目Owner书面确认不得修改*