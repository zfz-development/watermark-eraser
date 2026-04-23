<template>
	<view class="card" @click="goResult">
		<view class="card-left">
			<text class="card-type-icon">{{ task.file_type === 'image' ? '&#x1F5BC;' : '&#x1F3AC;' }}</text>
		</view>
		<view class="card-body">
			<view class="card-top">
				<text class="card-id">#{{ task.task_id }}</text>
				<text :class="['card-status', 'status-' + task.status]">{{ statusLabel }}</text>
			</view>
			<text class="card-name">{{ task.file_type === 'image' ? '图片' : '视频' }} - {{ fmtTime(task.created_at) }}</text>
			<text class="card-cost">消耗 {{ task.cost_points }} 积分</text>
		</view>
	</view>
</template>

<script>
	export default {
		props: {
			task: {
				type: Object,
				default: function() { return {} }
			}
		},
		computed: {
			statusLabel: function() {
				var map = { pending: '排队中', processing: '处理中', done: '已完成', failed: '失败', pending_config: '配置中' }
				return map[this.task.status] || this.task.status
			}
		},
		methods: {
			fmtTime: function(t) {
				if (!t) return ''
				return t.replace('T', ' ').slice(0, 16)
			},
			goResult: function() {
				if (this.task.status === 'done') {
					uni.navigateTo({ url: '/pages/result/index?task_id=' + this.task.task_id })
				}
			}
		}
	}
</script>

<style scoped>
	.card { display: flex; align-items: center; gap: 20rpx; background: #fff; border-radius: 16rpx; padding: 24rpx; }
	.card-left { font-size: 40rpx; }
	.card-body { flex: 1; }
	.card-top { display: flex; justify-content: space-between; align-items: center; }
	.card-id { font-size: 26rpx; color: #333; font-weight: bold; }
	.card-status { font-size: 22rpx; padding: 4rpx 16rpx; border-radius: 20rpx; }
	.status-pending { background: #FEF3C7; color: #92400E; }
	.status-processing { background: #DBEAFE; color: #1E40AF; }
	.status-done { background: #D1FAE5; color: #065F46; }
	.status-failed { background: #FEE2E2; color: #991B1B; }
	.status-pending_config { background: #F3F4F6; color: #666; }
	.card-name { font-size: 24rpx; color: #999; margin-top: 8rpx; display: block; }
	.card-cost { font-size: 22rpx; color: #ccc; margin-top: 4rpx; display: block; }
</style>
