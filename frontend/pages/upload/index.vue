<template>
	<view class="container">
		<view class="page-header">
			<text class="page-title">上传文件</text>
			<text class="page-desc">选择需要去除水印的图片或视频</text>
		</view>
		<view v-if="!fileInfo" class="upload-area" @tap="chooseFile">
			<view class="upload-icon-wrap">
				<text class="upload-plus">+</text>
			</view>
			<text class="upload-main-text">点击选择文件</text>
			<text class="upload-sub-text">支持 JPG / PNG / WEBP / MP4</text>
			<view class="upload-formats">
				<text class="format-tag">JPG</text>
				<text class="format-tag">PNG</text>
				<text class="format-tag">WEBP</text>
				<text class="format-tag">MP4</text>
			</view>
		</view>
		<view v-else class="preview-card">
			<view class="preview-header">
				<text class="preview-title">文件预览</text>
				<view class="file-type-badge">
					<text>{{ fileInfo.file_type === 'image' ? '图片' : '视频' }}</text>
				</view>
			</view>
			<image v-if="fileInfo.file_type==='image'" :src="previewUrl" mode="widthFix" class="preview-img"></image>
			<video v-else :src="previewUrl" class="preview-video" :controls="true"></video>
			<view class="file-meta">
				<text class="file-name">{{ fileInfo.file_name }}</text>
				<text class="file-size">{{ formatSize(fileInfo.file_size) }}</text>
			</view>
			<view class="quality-section" v-if="fileInfo.file_type==='image'">
				<text class="section-label">输出质量</text>
				<view class="quality-pills">
					<view :class="['quality-pill', quality==='standard'?'active':'']" @tap="quality='standard'">
						<text class="pill-name">标准</text>
						<text class="pill-cost">1 积分</text>
					</view>
					<view :class="['quality-pill', quality==='hd'?'active':'']" @tap="quality='hd'">
						<text class="pill-tag">推荐</text>
						<text class="pill-name">高清</text>
						<text class="pill-cost">3 积分</text>
					</view>
				</view>
			</view>
			<view class="cost-bar">
				<view class="cost-item">
					<text class="cost-label">预计消耗</text>
					<text class="cost-value">{{ costPoints }}</text>
					<text class="cost-unit">积分</text>
				</view>
				<view class="cost-divider"></view>
				<view class="cost-item">
					<text class="cost-label">当前余额</text>
					<text class="cost-value balance">{{ userPoints }}</text>
					<text class="cost-unit">积分</text>
				</view>
			</view>
			<button class="action-btn action-primary" @tap="submit" :loading="submitting">{{ submitting ? '处理中...' : '开始去水印' }}</button>
			<button class="action-btn action-secondary" @tap="reset">重新选择</button>
		</view>
	</view>
</template>

<script>
	import * as taskApi from '../../api/task.js'
	import * as userApi from '../../api/user.js'
	import * as userStore from '../../store/user.js'

	export default {
		data: function() {
			return {
				fileInfo: null,
				previewUrl: '',
				quality: 'standard',
				submitting: false,
				tempFilePath: ''
			}
		},
		computed: {
			costPoints: function() {
				if (!this.fileInfo) return 0
				if (this.fileInfo.file_type === 'image') return this.quality === 'standard' ? 1 : 3
				var dur = this.fileInfo.duration || 0
				if (dur <= 30) return 5
				if (dur <= 180) return 15
				return 30
			},
			userPoints: function() {
				var store = userStore.useUserStore()
				return store.userInfo ? store.userInfo.points : 0
			}
		},
		onShow: function() {
			this.loadProfile()
		},
		methods: {
			loadProfile: function() {
				var self = this
				if (userStore.useUserStore().isLoggedIn) {
					userApi.getProfile().then(function(user) {
						userStore.useUserStore().setUser(user)
					}).catch(function() {})
				}
			},
			chooseFile: function() {
				var self = this
				// #ifdef H5
				self.chooseFileH5()
				return
				// #endif
				uni.chooseImage({
					count: 1,
					success: function(res) {
						self.tempFilePath = res.tempFilePaths[0]
						self.doUpload(self.tempFilePath)
					}
				})
			},
			chooseFileH5: function() {
				var self = this
				var input = document.createElement('input')
				input.type = 'file'
				input.accept = 'image/*,video/mp4'
				input.style.display = 'none'
				document.body.appendChild(input)
				input.onchange = function(e) {
					var file = e.target.files[0]
					if (!file) { document.body.removeChild(input); return }
					var url = URL.createObjectURL(file)
					self.tempFilePath = url
					self.doUpload(url)
					document.body.removeChild(input)
				}
				input.click()
			},
			doUpload: function(filePath) {
				var self = this
				uni.showLoading({ title: '上传中...' })
				taskApi.uploadFile(filePath).then(function(info) {
					self.fileInfo = info
					self.previewUrl = filePath
					// Stay on upload page to show preview, do NOT auto-navigate
				}).catch(function() {
					uni.showToast({ title: '上传失败', icon: 'none' })
				}).finally(function() {
					uni.hideLoading()
				})
			},
			submit: function() {
				if (!this.fileInfo || this.submitting) return
				this.submitting = true
				var self = this
				if (self.fileInfo.file_type === 'image') {
					uni.navigateTo({ url: '/pages/mask-select/index?file_id=' + self.fileInfo.file_id + '&preview_url=' + encodeURIComponent(self.previewUrl) })
					self.submitting = false
					return
				}
				taskApi.removeWatermark(self.fileInfo.file_id, undefined, self.quality).then(function(result) {
					uni.navigateTo({ url: '/pages/result/index?task_id=' + result.task_id })
				}).catch(function() {
					uni.showToast({ title: '提交失败', icon: 'none' })
				}).finally(function() {
					self.submitting = false
				})
			},
			formatSize: function(bytes) {
				if (bytes < 1024) return bytes + 'B'
				if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + 'KB'
				return (bytes/1024/1024).toFixed(1) + 'MB'
			},
			reset: function() {
				this.fileInfo = null
				this.previewUrl = ''
				this.quality = 'standard'
			}
		}
	}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f7f7fa; }
.page-header { padding: 20rpx 8rpx 32rpx; }
.page-title { font-size: 44rpx; font-weight: 800; color: #1e1b4b; display: block; }
.page-desc { font-size: 26rpx; color: #94a3b8; display: block; margin-top: 8rpx; }
.upload-area { border: 4rpx dashed #c7d2fe; border-radius: 32rpx; padding: 80rpx 40rpx; text-align: center; margin-top: 16rpx; background: linear-gradient(135deg, #EEF2FF 0%, #fff 100%); }
.upload-area:active { transform: scale(0.98); border-color: #6366F1; }
.upload-icon-wrap { width: 120rpx; height: 120rpx; margin: 0 auto 28rpx; background: linear-gradient(135deg, #4F46E5, #7C3AED); border-radius: 32rpx; display: flex; align-items: center; justify-content: center; box-shadow: 0 12rpx 32rpx rgba(79,70,229,0.25); }
.upload-plus { font-size: 72rpx; color: #fff; font-weight: 300; }
.upload-main-text { display: block; font-size: 34rpx; color: #1e1b4b; font-weight: 700; }
.upload-sub-text { display: block; font-size: 24rpx; color: #94a3b8; margin-top: 12rpx; }
.upload-formats { margin-top: 28rpx; display: flex; justify-content: center; gap: 16rpx; }
.format-tag { font-size: 22rpx; color: #6366F1; background: #EEF2FF; padding: 8rpx 24rpx; border-radius: 20rpx; font-weight: 600; }
.preview-card { background: #fff; border-radius: 28rpx; padding: 32rpx; margin-top: 16rpx; box-shadow: 0 8rpx 40rpx rgba(0,0,0,0.06); }
.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24rpx; }
.preview-title { font-size: 30rpx; font-weight: 700; color: #1e1b4b; }
.file-type-badge { background: linear-gradient(135deg, #EEF2FF, #E0E7FF); color: #4F46E5; font-size: 22rpx; font-weight: 700; padding: 8rpx 20rpx; border-radius: 12rpx; }
.preview-img { width: 100%; border-radius: 20rpx; }
.preview-video { width: 100%; border-radius: 20rpx; height: 420rpx; }
.file-meta { display: flex; justify-content: space-between; align-items: center; padding: 24rpx 0 0; }
.file-name { font-size: 26rpx; color: #374151; font-weight: 500; flex: 1; overflow: hidden; white-space: nowrap; margin-right: 16rpx; }
.file-size { font-size: 24rpx; color: #94a3b8; }
.quality-section { margin-top: 32rpx; padding-top: 28rpx; border-top: 2rpx solid #f1f5f9; }
.section-label { font-size: 28rpx; font-weight: 700; color: #1e1b4b; display: block; margin-bottom: 16rpx; }
.quality-pills { display: flex; gap: 20rpx; }
.quality-pill { flex: 1; padding: 24rpx; text-align: center; border: 3rpx solid #e2e8f0; border-radius: 20rpx; background: #f8fafc; position: relative; }
.quality-pill.active { border-color: #4F46E5; background: linear-gradient(135deg, #EEF2FF, #E0E7FF); box-shadow: 0 4rpx 16rpx rgba(79,70,229,0.15); }
.pill-tag { position: absolute; top: -12rpx; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #F59E0B, #D97706); color: #fff; font-size: 18rpx; font-weight: 700; padding: 4rpx 16rpx; border-radius: 8rpx; }
.pill-name { display: block; font-size: 28rpx; color: #374151; font-weight: 600; margin-bottom: 4rpx; }
.pill-cost { display: block; font-size: 22rpx; color: #94a3b8; }
.cost-bar { display: flex; align-items: center; margin-top: 32rpx; padding: 28rpx; background: #f8fafc; border-radius: 20rpx; }
.cost-item { flex: 1; text-align: center; }
.cost-label { display: block; font-size: 24rpx; color: #94a3b8; text-align: center; }
.cost-value { font-size: 40rpx; font-weight: 800; color: #F59E0B; text-align: center; }
.cost-value.balance { color: #10B981; }
.cost-unit { font-size: 22rpx; color: #94a3b8; }
.cost-divider { width: 2rpx; height: 56rpx; background: #e2e8f0; }
.action-btn { margin-top: 28rpx; border-radius: 50rpx; height: 96rpx; line-height: 96rpx; font-size: 32rpx; font-weight: 700; letter-spacing: 2rpx; }
.action-primary { background: linear-gradient(135deg, #4F46E5, #7C3AED); color: #fff; box-shadow: 0 12rpx 32rpx rgba(79,70,229,0.35); }
.action-primary:active { transform: scale(0.97); }
.action-secondary { background: #fff; color: #64748b; border: 2rpx solid #e2e8f0; }
</style>