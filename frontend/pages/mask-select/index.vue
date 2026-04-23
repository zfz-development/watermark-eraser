<template>
	<view class="container">
		<view class="page-header">
			<text class="page-title">标记水印区域</text>
			<text class="page-desc">用手指框选图片上的水印位置，可多选</text>
		</view>
		<view class="canvas-area" @touchstart="onTouchStart" @touchmove="onTouchMove" @touchend="onTouchEnd" @mousedown="onMouseDown" @mousemove="onMouseMove" @mouseup="onMouseUp">
			<image :src="imageUrl" mode="widthFix" class="source-img" @load="onImageLoad"></image>
			<view v-for="(rect, idx) in rects" :key="idx" class="rect-box" :style="rectStyle(rect)">
				<view class="rect-label" @tap.stop="removeRect(idx)"><text class="label-text">x</text></view>
			</view>
			<view v-if="drawing" class="rect-box rect-current" :style="rectStyle(currentRect)"></view>
		</view>
		<view class="toolbar">
			<text class="rect-count">已选择 {{ rects.length }} 个区域</text>
			<view class="tool-buttons">
				<view class="tool-btn" @tap="undoRect"><text class="tool-icon">&#x21A9;</text><text class="tool-label">撤销</text></view>
				<view class="tool-btn" @tap="clearRects"><text class="tool-icon">&#x2716;</text><text class="tool-label">清除</text></view>
			</view>
		</view>
		<view class="bottom-bar">
			<button class="action-btn btn-skip" @tap="skipMask">自动检测</button>
			<button class="action-btn btn-confirm" :disabled="rects.length===0" @tap="confirmMask">确认选择</button>
		</view>
	</view>
</template>
<script>
import * as taskApi from '../../api/task.js'

export default {
	data: function() {
		return { fileId: '', imageUrl: '', scaleX: 1, scaleY: 1, rects: [], drawing: false, startX: 0, startY: 0, currentRect: null, _areaRect: null }
	},
	onLoad: function(q) {
		this.fileId = q.file_id || ''
		this.imageUrl = q.preview_url || ''
	},
	methods: {
		onImageLoad: function(e) {
			var self = this
			uni.getSystemInfo({ success: function(s) {
				var dw = s.windowWidth - 64
				self.scaleX = e.detail.width / dw
				self.scaleY = self.scaleX
			}})
			// get canvas area position for PC mouse events
			uni.createSelectorQuery().in(this).select('.canvas-area').boundingClientRect(function(rect) {
				self._areaRect = rect
			}).exec()
		},
		getPos: function(e) {
			var t = e.touches ? e.touches[0] : (e.changedTouches ? e.changedTouches[0] : e)
			if (!t) return { x: 0, y: 0 }
			var query = uni.createSelectorQuery().in(this)
			query.select('.canvas-area').boundingClientRect(function(rect) {
				this._areaRect = rect
			}.bind(this)).exec()
			var area = this._areaRect || { left: 0, top: 0 }
			return { x: t.clientX - area.left, y: t.clientY - area.top }
		},
		onTouchStart: function(e) {
			this.drawing = true
			var p = this.getPos(e)
			this.startX = p.x; this.startY = p.y
			this.currentRect = { x: p.x, y: p.y, w: 0, h: 0 }
		},
		onTouchMove: function(e) {
			if (!this.drawing) return
			e.preventDefault && e.preventDefault()
			var p = this.getPos(e)
			this.currentRect = { x: Math.min(this.startX, p.x), y: Math.min(this.startY, p.y), w: Math.abs(p.x - this.startX), h: Math.abs(p.y - this.startY) }
		},
		onTouchEnd: function() {
			this.drawing = false
			if (this.currentRect && this.currentRect.w > 10 && this.currentRect.h > 10) {
				this.rects.push({ x: this.currentRect.x, y: this.currentRect.y, w: this.currentRect.w, h: this.currentRect.h })
			}
			this.currentRect = null
		},
		onMouseDown: function(e) { this.onTouchStart(e) },
		onMouseMove: function(e) { this.onTouchMove(e) },
		onMouseUp: function(e) { this.onTouchEnd(e) },
		rectStyle: function(r) { return 'left:' + r.x + 'px;top:' + r.y + 'px;width:' + r.w + 'px;height:' + r.h + 'px' },
		toReal: function(r) { return [Math.round(r.x * this.scaleX), Math.round(r.y * this.scaleY), Math.round((r.x + r.w) * this.scaleX), Math.round((r.y + r.h) * this.scaleY)] },
		removeRect: function(i) { this.rects.splice(i, 1) },
		undoRect: function() { this.rects.pop() },
		clearRects: function() { this.rects = [] },
		confirmMask: function() {
			if (!this.rects.length) return
			var mask = this.rects.map(this.toReal.bind(this))
			this.goResult(JSON.stringify(mask))
		},
		skipMask: function() { this.goResult(null) },
		goResult: function(mask) {
			var self = this
			taskApi.removeWatermark(self.fileId, mask).then(function(r) {
				uni.navigateTo({ url: '/pages/result/index?task_id=' + r.task_id })
			}).catch(function() { uni.showToast({ title: '提交失败', icon: 'none' }) })
		}
	}
}
</script>
<style scoped>
.container { padding: 0 32rpx; min-height: 100vh; background: #f7f7fa; padding-bottom: 200rpx; }
.page-header { padding: 20rpx 8rpx 24rpx; }
.page-title { font-size: 40rpx; font-weight: 800; color: #1e1b4b; display: block; }
.page-desc { font-size: 26rpx; color: #94a3b8; display: block; margin-top: 8rpx; }
.canvas-area { position: relative; margin: 16rpx 0; border-radius: 20rpx; overflow: hidden; background: #fff; box-shadow: 0 8rpx 40rpx rgba(0,0,0,0.06); }
.source-img { width: 100%; display: block; }
.rect-box { position: absolute; border: 4rpx solid rgba(239,68,68,0.8); background: rgba(239,68,68,0.15); box-sizing: border-box; }
.rect-current { border-style: dashed; background: rgba(239,68,68,0.25); }
.rect-label { position: absolute; top: -24rpx; right: -4rpx; width: 36rpx; height: 36rpx; background: #EF4444; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.label-text { color: #fff; font-size: 22rpx; font-weight: 700; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin: 20rpx 0; padding: 20rpx 28rpx; background: #fff; border-radius: 20rpx; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04); }
.rect-count { font-size: 28rpx; color: #374151; font-weight: 600; }
.tool-buttons { display: flex; gap: 16rpx; }
.tool-btn { display: flex; flex-direction: column; align-items: center; padding: 12rpx 24rpx; }
.tool-icon { font-size: 36rpx; color: #64748b; }
.tool-label { font-size: 20rpx; color: #94a3b8; margin-top: 4rpx; }
.bottom-bar { position: fixed; bottom: 0; left: 0; right: 0; display: flex; gap: 16rpx; padding: 20rpx 32rpx; padding-bottom: calc(20rpx + env(safe-area-inset-bottom)); background: #fff; box-shadow: 0 -4rpx 20rpx rgba(0,0,0,0.08); }
.action-btn { flex: 1; border-radius: 50rpx; height: 88rpx; line-height: 88rpx; font-size: 30rpx; font-weight: 700; border: none; }
.btn-skip { background: #f1f5f9; color: #64748b; }
.btn-confirm { background: linear-gradient(135deg, #4F46E5, #7C3AED); color: #fff; box-shadow: 0 8rpx 24rpx rgba(79,70,229,0.35); }
.btn-confirm[disabled] { opacity: 0.4; box-shadow: none; }
</style>
