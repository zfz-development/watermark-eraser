<template>
	<view class="container">
		<view class="page-header">
			<text class="page-title">历史记录</text>
			<text class="page-desc">查看所有去水印处理记录</text>
		</view>
		<view class="tabs">
			<view :class="['tab', filter===''?'active':'']" @tap="setFilter('')">全部</view>
			<view :class="['tab', filter==='image'?'active':'']" @tap="setFilter('image')">图片</view>
			<view :class="['tab', filter==='video'?'active':'']" @tap="setFilter('video')">视频</view>
		</view>
		<view class="list">
			<view v-for="(item, index) in tasks" :key="item.task_id" class="task-card" @tap="goResult(item.task_id)">
				<view :class="['task-status', 'status-'+item.status]">
					<text>{{ statusLabel(item.status) }}</text>
				</view>
				<view class="task-body">
					<text class="task-type-icon">{{ item.file_type === 'image' ? '&#x1F5BC;' : '&#x1F3AC;' }}</text>
					<view class="task-info">
						<text class="task-type">{{ item.file_type === 'image' ? '图片去水印' : '视频去水印' }}</text>
						<text class="task-time">{{ formatTime(item.created_at) }}</text>
					</view>
				</view>
				<text class="task-cost">{{ item.cost_points }} 积分</text>
			</view>
			<view v-if="tasks.length === 0" class="empty">
				<text class="empty-icon">&#x1F4CB;</text>
				<text class="empty-text">暂无处理记录</text>
				<text class="empty-hint">去水印后的记录将显示在这里</text>
			</view>
		</view>
	</view>
</template>

<script>
	import * as taskApi from '../../api/task.js'

	export default {
		data: function() {
			return {
				tasks: [],
				filter: '',
				page: 1
			}
		},
		onShow: function() {
			this.page = 1
			this.tasks = []
			this.loadTasks()
		},
		watch: {
			filter: function() {
				this.page = 1
				this.tasks = []
				this.loadTasks()
			}
		},
		methods: {
			setFilter: function(val) {
				this.filter = val
			},
			loadTasks: function() {
				var self = this
				var params = { page: self.page, page_size: 20 }
				if (self.filter) params.status = self.filter
				taskApi.getTasks(params).then(function(res) {
					self.tasks = self.tasks.concat(res.items || [])
				}).catch(function() {})
			},
			goResult: function(id) {
				uni.navigateTo({ url: '/pages/result/index?task_id=' + id })
			},
			statusLabel: function(s) {
				var map = { pending: '排队中', processing: '处理中', done: '已完成', failed: '失败', pending_config: '配置中' }
				return map[s] || s
			},
			formatTime: function(t) {
				if (!t) return ''
				var d = new Date(t)
				return (d.getMonth()+1) + '/' + d.getDate() + ' ' + String(d.getHours()).padStart(2,'0') + ':' + String(d.getMinutes()).padStart(2,'0')
			}
		}
	}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f7f7fa; }
.page-header { padding: 20rpx 8rpx 28rpx; }
.page-title { font-size: 44rpx; font-weight: 800; color: #1e1b4b; display: block; }
.page-desc { font-size: 26rpx; color: #94a3b8; display: block; margin-top: 8rpx; }
.tabs { display: flex; gap: 0; margin-bottom: 28rpx; padding: 6rpx; background: #fff; border-radius: 20rpx; box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.04); }
.tab { flex: 1; padding: 20rpx 0; border-radius: 16rpx; font-size: 28rpx; color: #64748b; background: transparent; text-align: center; font-weight: 500; }
.tab.active { background: linear-gradient(135deg, #4F46E5, #7C3AED); color: #fff; font-weight: 700; box-shadow: 0 4rpx 16rpx rgba(79,70,229,0.3); }
.task-card { background: #fff; border-radius: 24rpx; padding: 32rpx; margin-bottom: 20rpx; display: flex; align-items: center; gap: 20rpx; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04); }
.task-card:active { transform: scale(0.98); }
.task-status { font-size: 22rpx; padding: 10rpx 20rpx; border-radius: 12rpx; font-weight: 700; white-space: nowrap; }
.status-pending, .status-processing, .status-pending_config { color: #4F46E5; background: linear-gradient(135deg, #EEF2FF, #E0E7FF); }
.status-done { color: #059669; background: linear-gradient(135deg, #D1FAE5, #A7F3D0); }
.status-failed { color: #EF4444; background: linear-gradient(135deg, #FEE2E2, #FECACA); }
.task-body { flex: 1; display: flex; align-items: center; gap: 16rpx; }
.task-type-icon { font-size: 36rpx; }
.task-info { flex: 1; }
.task-type { display: block; font-size: 28rpx; color: #1e293b; font-weight: 600; }
.task-time { display: block; font-size: 22rpx; color: #94a3b8; margin-top: 4rpx; }
.task-cost { font-size: 26rpx; color: #F59E0B; font-weight: 800; }
.empty { text-align: center; padding: 120rpx 40rpx; }
.empty-icon { font-size: 80rpx; display: block; margin-bottom: 20rpx; }
.empty-text { font-size: 30rpx; color: #94a3b8; display: block; font-weight: 600; }
.empty-hint { font-size: 24rpx; color: #cbd5e1; display: block; margin-top: 8rpx; }
</style>