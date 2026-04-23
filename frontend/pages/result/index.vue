<template>
	<view class="container">
		<view class="status-section">
			<view class="status-icon-ring">
				<text class="status-icon">{{ statusIcon }}</text>
			</view>
			<text class="status-text">{{ statusText }}</text>
			<text v-if="task.status==='processing'" class="status-sub">AI 正在努力处理中，请稍候...</text>
		</view>
		<view v-if="task.status==='done'" class="result-card">
			<view class="result-header">
				<text class="result-label">处理完成</text>
				<view class="result-badge">
					<text class="badge-text">高清输出</text>
				</view>
			</view>
			<image v-if="task.file_type==='image'" :src="task.output_url" mode="widthFix" class="result-img"></image>
			<video v-else :src="task.output_url" class="result-video" :controls="true"></video>
			<view class="result-actions">
				<button class="btn btn-save" @tap="download">
					<text class="btn-ico">&#x1F4E5;</text>
					<text> 保存到相册</text>
				</button>
				<button class="btn btn-again" @tap="goUpload">
					<text class="btn-ico">&#x1F504;</text>
					<text> 继续处理</text>
				</button>
			</view>
		</view>
		<view v-if="task.status==='pending_config'" class="info-card">
			<text class="info-icon">&#x1F514;</text>
			<text class="info-title">引擎配置中</text>
			<text class="info-desc">去水印引擎正在初始化，请稍后再试</text>
		</view>
		<view v-if="task.status==='failed'" class="info-card info-error">
			<text class="info-icon">&#x26A0;</text>
			<text class="info-title">处理失败</text>
			<text class="info-desc">{{ task.error_msg || '处理过程中出现错误' }}</text>
			<view class="refund-tag">
				<text>积分已退回账户</text>
			</view>
		</view>
		<view v-if="task.status==='pending' || task.status==='processing'" class="progress-card">
			<view class="progress-bar-bg">
				<view class="progress-bar-fill"></view>
			</view>
			<text class="progress-hint">请勿关闭页面，处理完成后将自动显示结果</text>
		</view>
	</view>
</template>

<script>
	import * as taskApi from '../../api/task.js'

	export default {
		data: function() {
			return {
				taskId: 0,
				task: { status: 'pending', file_type: 'image', output_url: '', input_preview_url: '', cost_points: 0, error_msg: '', created_at: '', finished_at: '' },
				timer: null
			}
		},
		computed: {
			statusIcon: function() {
				var s = this.task.status
				if (s === 'pending' || s === 'processing') return '\u23F3'
				if (s === 'done') return '\u2705'
				if (s === 'failed') return '\u274C'
				return '\uD83D\uDD27'
			},
			statusText: function() {
				var s = this.task.status
				if (s === 'pending') return '排队等待中...'
				if (s === 'processing') return '正在处理中...'
				if (s === 'done') return '处理完成！'
				if (s === 'failed') return '处理失败'
				return '引擎配置中'
			}
		},
		onLoad: function(query) {
			this.taskId = parseInt(query.task_id)
		},
		onShow: function() {
			this.fetchTask()
			var self = this
			this.timer = setInterval(function() { self.fetchTask() }, 2000)
		},
		onHide: function() {
			if (this.timer) { clearInterval(this.timer); this.timer = null }
		},
		onUnload: function() {
			if (this.timer) { clearInterval(this.timer); this.timer = null }
		},
		methods: {
			fetchTask: function() {
				var self = this
				taskApi.getTask(self.taskId).then(function(data) {
					self.task = data
					if (['done', 'failed', 'pending_config'].indexOf(data.status) >= 0 && self.timer) {
						clearInterval(self.timer)
						self.timer = null
					}
				}).catch(function() {})
			},
			download: function() {
				var self = this
				var fileId = (self.task.output_url || '').split('/').pop()
				if (!fileId) return
				taskApi.downloadFile(fileId).then(function(filePath) {
					uni.saveImageToPhotosAlbum({
						filePath: filePath,
						success: function() { uni.showToast({ title: '已保存', icon: 'success' }) },
						fail: function() { uni.showToast({ title: '保存失败', icon: 'none' }) }
					})
				})
			},
			goUpload: function() {
				uni.switchTab({ url: '/pages/upload/index' })
			}
		}
	}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f7f7fa; }
.status-section { text-align: center; padding: 80rpx 0 48rpx; }
.status-icon-ring { width: 160rpx; height: 160rpx; margin: 0 auto; border-radius: 50%; background: linear-gradient(135deg, #EEF2FF, #E0E7FF); display: flex; align-items: center; justify-content: center; box-shadow: 0 12rpx 40rpx rgba(79,70,229,0.15); }
.status-icon { font-size: 80rpx; }
.status-text { display: block; font-size: 36rpx; color: #1e1b4b; margin-top: 28rpx; font-weight: 700; text-align: center; }
.status-sub { display: block; font-size: 26rpx; color: #94a3b8; margin-top: 8rpx; text-align: center; }
.result-card { background: #fff; border-radius: 28rpx; padding: 32rpx; box-shadow: 0 8rpx 40rpx rgba(0,0,0,0.06); }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24rpx; }
.result-label { font-size: 30rpx; font-weight: 700; color: #1e1b4b; }
.result-badge { background: linear-gradient(135deg, #10B981, #059669); padding: 6rpx 20rpx; border-radius: 12rpx; }
.badge-text { font-size: 22rpx; color: #fff; font-weight: 700; }
.result-img { width: 100%; border-radius: 20rpx; }
.result-video { width: 100%; height: 420rpx; border-radius: 20rpx; }
.result-actions { margin-top: 32rpx; display: flex; gap: 20rpx; }
.btn { flex: 1; border-radius: 50rpx; height: 96rpx; display: flex; align-items: center; justify-content: center; font-size: 30rpx; font-weight: 700; }
.btn-save { background: linear-gradient(135deg, #10B981, #059669); color: #fff; box-shadow: 0 8rpx 24rpx rgba(16,185,129,0.35); }
.btn-save:active { transform: scale(0.97); }
.btn-again { background: linear-gradient(135deg, #4F46E5, #7C3AED); color: #fff; box-shadow: 0 8rpx 24rpx rgba(79,70,229,0.35); }
.btn-again:active { transform: scale(0.97); }
.btn-ico { font-size: 32rpx; }
.info-card { text-align: center; padding: 60rpx 40rpx; background: #fff; border-radius: 28rpx; box-shadow: 0 8rpx 40rpx rgba(0,0,0,0.06); }
.info-error { border: 3rpx solid #FEE2E2; }
.info-icon { font-size: 72rpx; display: block; margin-bottom: 20rpx; text-align: center; }
.info-title { font-size: 32rpx; color: #1e1b4b; font-weight: 700; display: block; text-align: center; }
.info-desc { font-size: 26rpx; color: #94a3b8; display: block; margin-top: 12rpx; text-align: center; }
.refund-tag { display: inline-block; margin-top: 24rpx; background: #FEF3C7; color: #D97706; font-size: 24rpx; font-weight: 600; padding: 12rpx 28rpx; border-radius: 12rpx; }
.progress-card { background: #fff; border-radius: 28rpx; padding: 40rpx 32rpx; box-shadow: 0 8rpx 40rpx rgba(0,0,0,0.06); }
.progress-bar-bg { height: 12rpx; background: #f1f5f9; border-radius: 6rpx; overflow: hidden; margin-bottom: 24rpx; }
.progress-bar-fill { height: 100%; width: 40%; background: linear-gradient(90deg, #4F46E5, #7C3AED); border-radius: 6rpx; animation: prog 1.5s ease-in-out infinite; }
@keyframes prog { 0%,100% { width: 20%; } 50% { width: 60%; } }
.progress-hint { font-size: 24rpx; color: #94a3b8; text-align: center; display: block; }
</style>