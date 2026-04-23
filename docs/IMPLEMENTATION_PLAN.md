# 水印去除工具 - 完整实施方案 v1.0

> 创建日期: 2026-04-08
> 状态: 待确认

---

## 一、项目概述

一款面向 C 端用户的图片+视频 AI 去水印工具，先 H5 后扩展小程序，核心卖点：
- **一键操作**：上传 → 自动检测/框选 → 去除 → 下载
- **支持 AI 短剧截图/视频去水印**（当前市场热门需求）
- **高质量输出**：无损或近无损修复

---

## 二、技术架构

```
用户(H5/小程序)
    ↓ HTTPS
Nginx 反向代理
    ↓
FastAPI 后端 (Python)
    ├── 用户系统 (JWT 鉴权)
    ├── 任务系统 (异步队列 Celery + Redis)
    ├── 文件服务 (本地/OSS)
    ├── 去水印引擎 (策略模式，可替换)
    │   ├── 第三方 API 适配层 ← 当前
    │   └── 本地模型 (LaMa 等) ← 后续
    └── 计费系统
```

### 技术栈

| 层 | 技术 | 理由 |
|---|------|------|
| 前端 | uni-app (Vue3 + TypeScript) | 一套代码 H5 + 小程序 |
| 后端 | Python 3.11 + FastAPI | 图像处理生态 + 自动文档 |
| 数据库 | SQLite → MySQL | 前期零运维，后期可切换 |
| 缓存/队列 | Redis + Celery | 异步任务处理 |
| 文件存储 | 本地 → 阿里云 OSS | 前期本地，后期上云 |
| 部署 | Docker Compose | 一键部署 |

---

## 三、接口预留策略（去水印引擎）

### 策略模式设计

```python
# backend/app/services/watermark/base.py

from abc import ABC, abstractmethod
from typing import Optional

class WatermarkRemover(ABC):
    """去水印引擎基类 - 所有第三方/本地模型继承此类"""
    
    @abstractmethod
    async def remove_image_watermark(
        self, input_path: str, output_path: str,
        mask: Optional[list] = None  # 用户手动框选区域 [[x1,y1,x2,y2], ...]
    ) -> dict:
        """去除图片水印，返回 {success, output_path, cost_tokens}"""
        pass
    
    @abstractmethod
    async def remove_video_watermark(
        self, input_path: str, output_path: str,
        mask: Optional[list] = None
    ) -> dict:
        """去除视频水印（逐帧处理），返回同上"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def quota_remaining(self) -> int:
        """剩余额度"""
        pass
```

### 配置化切换

```yaml
# config.yaml
watermark:
  active_engine: "placeholder"
  engines:
    placeholder:
      class: "PlaceholderRemover"
      enabled: true
    remove_bg:
      class: "RemoveBgRemover"
      enabled: false
      api_key: "${REMOVE_BG_API_KEY}"
      base_url: "https://api.remove.bg/v1.0"
    watermarkremover_io:
      class: "WatermarkRemoverIORemover"
      enabled: false
      api_key: "${WMR_IO_API_KEY}"
    lama_local:
      class: "LaMaLocalRemover"
      enabled: false
      model_path: "/models/lama/big-lama"
      require_gpu: true
```

> **你拿到 API Key 后，改 config + enabled: true 即可，零代码改动。**

### PlaceholderRemover 行为
- 接收任务 → 立即返回 `status: "pending_config"`
- 前端展示："该功能正在配置中，请稍后再试"
- 不消耗用户额度

---

## 四、用户付费体系设计

### 4.1 行业调研（成熟案例参考）

| 产品 | 免费额度 | 付费模式 | 价格区间 | 特色活动 |
|------|---------|---------|---------|---------|
| **Remove.bg** | 1张/次，低分辨率 | 按量订阅 | $9-99/月 | 无 |
| **美图秀秀** | 有水印免费 | 会员去水印 | ¥15/月 | 新用户3天VIP |
| **稿定设计** | 有限免费 | 按次+会员 | ¥19-99/月 | 每日签到领次数 |
| **去水印大师(小程序)** | 3次/天 | 按次+包月 | ¥6/30次, ¥30/月 | 看广告换次数 |
| **一键去水印** | 1次/天 | 会员 | ¥12/月 | 邀请好友得次数 |

### 4.2 推荐收费模型

采用 **"免费体验 + 看广告 + 积分 + 会员"** 四层体系：

#### 层级一：免费体验（引流）
- 新用户注册送 **5 积分**
- 每日签到送 **1 积分**
- 邀请好友注册送 **3 积分**（双方都有）
- 首次使用引导完成送 **2 积分**

#### 层级二：看广告赚积分（广告变现）
- 每看一次激励视频获得 **2 积分**
- 每日看广告上限 **5 次**（防刷）
- 积分有效期：永久

#### 层级三：直接购买积分（按量付费）

| 积分包 | 价格 | 单价 |
|--------|------|------|
| 30 积分 | ¥6 | ¥0.20/次 |
| 100 积分 | ¥15 | ¥0.15/次 |
| 500 积分 | ¥50 | ¥0.10/次 |
| 2000 积分 | ¥150 | ¥0.075/次 |

#### 层级四：VIP 会员（订阅制）

| 会员档 | 月费 | 包含 | 额外特权 |
|--------|------|------|---------|
| 基础 VIP | ¥19/月 | 200次图片 + 20次视频 | 高优先级队列 |
| 专业 VIP | ¥39/月 | 1000次图片 + 100次视频 | 批量处理 + API |
| 年费 VIP | ¥199/年 | 不限图片 + 500视频/月 | 所有功能 |

#### 积分消耗规则

| 操作 | 消耗积分 | 说明 |
|------|---------|------|
| 图片去水印 | 1 | 单张 ≤ 10MB |
| 图片去水印(高清) | 3 | 单张 ≤ 30MB，高分辨率输出 |
| 视频去水印(≤30秒) | 5 | 成本较高 |
| 视频去水印(≤3分钟) | 15 | |
| 视频去水印(>3分钟) | 30 | |
| 批量处理(+10张) | 额外 ×0.8 | 会员专属 |

### 4.3 数据库设计

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    phone         VARCHAR(20) UNIQUE,
    wechat_openid VARCHAR(64) UNIQUE,
    nickname      VARCHAR(50),
    avatar_url    VARCHAR(255),
    points        INTEGER DEFAULT 0,
    vip_level     INTEGER DEFAULT 0,
    vip_expire_at DATETIME,
    invite_code   VARCHAR(8) UNIQUE,
    invited_by    INTEGER REFERENCES users(id),
    total_used    INTEGER DEFAULT 0,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE point_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    amount     INTEGER NOT NULL,
    type       VARCHAR(30) NOT NULL,
    detail     VARCHAR(255),
    task_id    INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    file_type     VARCHAR(10) NOT NULL,
    engine        VARCHAR(30) DEFAULT 'placeholder',
    status        VARCHAR(20) DEFAULT 'pending',
    input_url     VARCHAR(500),
    output_url    VARCHAR(500),
    input_size    INTEGER,
    cost_points   INTEGER DEFAULT 0,
    error_msg     VARCHAR(500),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    finished_at   DATETIME
);

CREATE TABLE vip_orders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    level         INTEGER NOT NULL,
    duration      INTEGER NOT NULL,
    amount        DECIMAL(10,2) NOT NULL,
    pay_method    VARCHAR(20),
    pay_status    VARCHAR(20) DEFAULT 'pending',
    trade_no      VARCHAR(64),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE point_orders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    points        INTEGER NOT NULL,
    amount        DECIMAL(10,2) NOT NULL,
    pay_method    VARCHAR(20),
    pay_status    VARCHAR(20) DEFAULT 'pending',
    trade_no      VARCHAR(64),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sign_in_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    date       DATE NOT NULL,
    reward     INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);
```

### 4.4 接口设计（含付费相关）

```
=== 用户系统 ===
POST   /api/v1/user/register
POST   /api/v1/user/login
POST   /api/v1/user/wechat-login       # 预留
GET    /api/v1/user/profile

=== 积分系统 ===
GET    /api/v1/user/points
GET    /api/v1/user/points/logs
POST   /api/v1/user/sign-in
POST   /api/v1/user/invite
POST   /api/v1/user/ad-reward          # 预留

=== 商城 ===
GET    /api/v1/shop/packages
GET    /api/v1/shop/vip-plans
POST   /api/v1/shop/order/points
POST   /api/v1/shop/order/vip
POST   /api/v1/shop/order/callback     # 预留

=== 核心业务 ===
POST   /api/v1/upload
POST   /api/v1/watermark/remove
GET    /api/v1/task/{id}
GET    /api/v1/tasks
DELETE /api/v1/task/{id}
GET    /api/v1/download/{id}

=== 管理后台（预留）===
GET    /api/v1/admin/stats
GET    /api/v1/admin/users
POST   /api/v1/admin/config
```

---

## 五、项目目录结构

```
watermark-eraser/
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   ├── API_SPEC.md
│   ├── DATABASE_DESIGN.md
│   ├── UI_SPEC.md
│   └── DEPLOY_GUIDE.md
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── task.py
│   │   │   ├── order.py
│   │   │   └── point.py
│   │   ├── routers/
│   │   │   ├── user.py
│   │   │   ├── points.py
│   │   │   ├── shop.py
│   │   │   ├── task.py
│   │   │   ├── upload.py
│   │   │   └── admin.py
│   │   ├── services/
│   │   │   ├── auth.py
│   │   │   ├── point_service.py
│   │   │   ├── payment_service.py
│   │   │   └── watermark/
│   │   │       ├── __init__.py
│   │   │       ├── base.py
│   │   │       ├── placeholder.py
│   │   │       ├── remove_bg.py
│   │   │       ├── wmr_io.py
│   │   │       └── lama_local.py
│   │   ├── tasks/
│   │   │   ├── watermark_task.py
│   │   │   └── cleanup_task.py
│   │   └── utils/
│   │       ├── file.py
│   │       ├── video.py
│   │       └── response.py
│   ├── config.yaml
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index/
│   │   │   ├── upload/
│   │   │   ├── result/
│   │   │   ├── history/
│   │   │   ├── shop/
│   │   │   ├── vip/
│   │   │   ├── sign-in/
│   │   │   └── mine/
│   │   ├── api/
│   │   │   ├── index.ts
│   │   │   ├── user.ts
│   │   │   ├── task.ts
│   │   │   ├── shop.ts
│   │   │   └── points.ts
│   │   ├── components/
│   │   │   ├── FileUploader.vue
│   │   │   ├── ImageCropper.vue
│   │   │   ├── VideoPlayer.vue
│   │   │   ├── PointBadge.vue
│   │   │   └── AdButton.vue
│   │   ├── store/
│   │   ├── utils/
│   │   ├── static/
│   │   └── App.vue
│   ├── manifest.json
│   ├── pages.json
│   ├── package.json
│   └── tsconfig.json
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 六、实施计划

### Phase 1：基础框架 + 核心去水印（5天）

| 天 | 后端任务 | 前端任务 |
|----|---------|---------|
| D1 | FastAPI 骨架 + 数据库建表 + JWT 鉴权 | uni-app 初始化 + 路由 + 登录页 |
| D2 | 上传接口 + 文件管理 | 上传组件 + 文件校验 |
| D3 | 去水印引擎框架(策略模式) + Placeholder | 上传页 UI + 任务提交 |
| D4 | 任务系统 + 异步队列 | 结果页 + 历史页 |
| D5 | 接口联调 + bug修复 | 联调 + bug修复 |

**里程碑**：能上传文件，任务状态流转正常（引擎为 placeholder）

### Phase 2：接入真实去水印 API（2天）

| 天 | 任务 |
|----|------|
| D6 | API Key → 配置引擎 → RemoveBgRemover 实现 |
| D7 | 视频去水印适配（逐帧处理）+ 联调测试 |

**里程碑**：完整去水印流程可用

### Phase 3：用户付费体系（5天）

| 天 | 后端任务 | 前端任务 |
|----|---------|---------|
| D8 | 积分系统 + 签到 + 邀请 | 个人中心 + 积分显示 |
| D9 | 积分商城 + 订单系统 | 商城页 + 套餐展示 |
| D10 | VIP 会员 + 额度判断 | VIP 页 + 支付流程 UI |
| D11 | 广告奖励接口（预留） | 广告按钮 + 奖励弹窗（预留） |
| D12 | 付费体系联调 + 测试 | 联调 + 测试 |

**里程碑**：完整付费体系可用（支付用模拟模式）

### Phase 4：优化 + 部署（3天）

| 天 | 任务 |
|----|------|
| D13 | 错误处理 + 日志 + 性能优化 |
| D14 | UI 打磨 + 兼容性测试 |
| D15 | Docker 部署 + 域名 + 线上测试 |

**里程碑**：系统上线

**总计：15 个工作日 ≈ 3 周**

---

## 七、风险管控

| 风险 | 概率 | 影响 | 应对方案 |
|------|------|------|---------|
| API Key 申请延迟 | 高 | 低 | Placeholder 引擎兜底 |
| 视频去水印效果差 | 中 | 中 | 多引擎 fallback + 手动框选 |
| 第三方 API 涨价/停服 | 低 | 高 | 策略模式 + 本地模型备选 |
| 支付接口审核慢 | 中 | 中 | 先免费版积累用户 |
| 小程序审核不通过 | 中 | 中 | H5 先行 |
| 服务器成本超预期 | 低 | 中 | 文件清理 + CDN + 免费额度 |
| 版权纠纷 | 低 | 高 | 用户协议 + 免责 + 举报 |

---

## 八、成本估算

### 开发期
- 服务器（2核4G）：≈ ¥100/月
- 域名 + SSL：≈ ¥50/年
- 第三方 API：免费额度内

### 月运营成本

| 项目 | 初期 | 1000 DAU |
|------|------|---------|
| 服务器 | ¥100 | ¥300-500 |
| 第三方 API | ¥0 | ¥500-2000 |
| OSS | ¥10 | ¥100-300 |
| 手续费 | 0.6% | 按收入 |
| **合计** | **≈¥120** | **≈¥1000-3000** |

### 盈亏平衡
- 1000 DAU, 付费转化率 3%, ARPU ¥30 → 月收入 ¥900
- 需 3000+ DAU 覆盖成本
- 广告收入可额外补充 ¥500-1000/月

---

## 九、下一步行动

- [ ] 确认本方案
- [ ] 产出 API_SPEC.md（详细接口规范）
- [ ] 注册 API Key（Remove.bg 等）
- [ ] 准备服务器
- [ ] 进入 Phase 1 开发
