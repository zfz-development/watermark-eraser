# watermark-eraser 版本记录

## FINAL — v19-optimized（2026-04-21 封版）

**GPU脚本 md5**: `68a3750f0aa2e456db57c299ed1cc97f`
**GPU备份**: `lama_inpaint.py.FINAL` + `lama_inpaint.py.bak.v19_optimized` (⚠️两者不同！FINAL=68a3750f 才是对的)
**用户评价**: "好多了，小图基本看不出来，只有大图放大原尺寸仔细看才能看出一点点细微痕迹"

### 参数
- 轮廓检测 findContours（矩形mask→提取轮廓填充）
- dilation (5,5) 1次
- ROI padding 300px
- **3次 LaMA inpainting pass**
- LAB 颜色校正，参考区 21x21
- **羽化 50px，余弦缓动 (cosine easing)**
- 多尺度边缘平滑 sigma 1.5 + 0.8
- 双边滤波保边纹理匹配
- ❌ 无 seamlessClone（已验证会把水印混回来）
- ❌ 无缩小放大（已验证会产生白色区块）

### 已知限制
- 大图（2730x1535）修复区域与周围背景有极细微色差，需放大到原尺寸才能看出
- 这是 LaMA 模型的能力上限，后处理优化已到平衡点，再加后处理反而更差

---

## 废弃版本（不要使用）

| 文件 | md5 | 问题 |
|------|-----|------|
| .bak.v19_optimized | 26e21b45 | 和FINAL不同，效果差，有清晰印记 |
| .bak.v19 | c5f33d24 | 原始V19，无cosine/无双边 |
| .bak.v18 | cbdc0d42 | 精确mask基础版 |
| .bak.v21 | 66e035e1 | 60px羽化+多尺度边缘+双边 |
| .bak.v22 | 66d8b149 | 去掉轮廓检测，直接矩形 |
| .bak.v23 | d97ad89d | 缩小到1024处理再放大（白色区块） |
| .bak.good | dd72fc5a | 最早的好版本 |

---

## 前端版本

### mask-select（2026-04-21）
- **路径**: `/opt/watermark-eraser/frontend/src/pages/mask-select/index.vue`
- **关键修复**: mask坐标用纯数学方式计算（容器宽度反算displayH=natH*(containerW/natW)），不用boundingClientRect
- **功能**: 删除按钮（@touchstart.stop.prevent）、全屏预览（H5原生img）、保存（H5 fetch+blob+anchor、原生downloadFile+saveImageToPhotosAlbum）
- **注意**: 修改后必须 `npx uni build -p h5` 编译

---

## 后续优化方向

### 1. 自动识别水印区域（用户优先级低，"放最后"）
- 用户框选后，自动检测框内真实水印文字像素
- 用 Laplacian 纹理检测或 OCR 定位文字
- 只对文字像素做 inpainting，不处理大块背景
- ⚠️ v24 尝试过 Laplacian 检测，效果更差，需要更精细的方案

### 2. 切换 SD 1.5 Inpainting 模型
- GPU 上已部署（AutoPipelineForInpainting）
- 对纹理生成能力比 LaMA 强，可能解决大图细微痕迹
- 需要后端 main.py 支持模型切换（已有 model=sd15 参数）
- 代价：速度更慢

### 3. 多模型融合
- LaMA 去水印 + SD 1.5 纹理填充
- 先用 LaMA 粗修，再用 SD 1.5 精修纹理
- 可能获得最佳效果但速度最慢
