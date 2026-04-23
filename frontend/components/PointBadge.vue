<template>
	<view class="badge">
		<text class="badge-icon">&#x1F4B0;</text>
		<text class="badge-num">{{ points }}</text>
		<text class="badge-unit">积分</text>
	</view>
</template>

<script>
	export default {
		props: {
			points: {
				type: Number,
				default: 0
			}
		}
	}
</script>

<style scoped>
	.badge { display: inline-flex; align-items: center; gap: 8rpx; background: #EEF2FF; border-radius: 30rpx; padding: 8rpx 20rpx; }
	.badge-icon { font-size: 28rpx; }
	.badge-num { font-size: 28rpx; font-weight: bold; color: #4F46E5; }
	.badge-unit { font-size: 22rpx; color: #4F46E5; }
</style>
