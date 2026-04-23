<template>
	<view class="container">
		<view class="page-header">
			<text class="page-title">积分商城</text>
			<text class="page-desc">购买积分，畅享去水印服务</text>
		</view>
		<view class="section">
			<view class="section-head">
				<text class="section-title">&#x1F381; 积分包</text>
			</view>
			<view class="packages">
				<view v-for="pkg in packages" :key="pkg.id" :class="['pkg-card', pkg.popular?'popular':'']" @tap="buyPoints(pkg)">
					<text v-if="pkg.badge" class="pkg-badge">{{ pkg.badge }}</text>
					<text class="pkg-name">{{ pkg.name }}</text>
					<text class="pkg-points">{{ pkg.points }} 积分</text>
					<view class="pkg-price-row">
						<text class="pkg-price">{{ pkg.price }}</text>
						<text class="pkg-yuan">元</text>
					</view>
					<text v-if="pkg.original_price" class="pkg-original">原价 {{ pkg.original_price }} 元</text>
				</view>
			</view>
		</view>
		<view class="section">
			<view class="section-head">
				<text class="section-title">&#x1F451; VIP 会员</text>
			</view>
			<view class="plans">
				<view v-for="plan in plans" :key="plan.id" class="plan-card" @tap="buyVip(plan)">
					<view class="plan-top">
						<text class="plan-name">{{ plan.name }}</text>
						<view class="plan-price-wrap">
							<text class="plan-price">{{ plan.price }}</text>
							<text class="plan-yuan">元</text>
						</view>
					</view>
					<text v-if="plan.original_price" class="plan-original">原价 {{ plan.original_price }} 元</text>
					<view class="plan-features">
						<view v-for="f in plan.features" :key="f" class="plan-feature">
							<text class="feature-check">&#x2713;</text>
							<text class="feature-text">{{ f }}</text>
						</view>
					</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import * as shopApi from '../../api/shop.js'

	export default {
		data: function() {
			return {
				packages: [],
				plans: []
			}
		},
		onShow: function() {
			this.loadData()
		},
		methods: {
			loadData: function() {
				var self = this
				shopApi.getPackages().then(function(data) { self.packages = data }).catch(function() {})
				shopApi.getVipPlans().then(function(data) { self.plans = data }).catch(function() {})
			},
			buyPoints: function(pkg) {
				var self = this
				shopApi.createPointOrder(pkg.id).then(function() {
					uni.showToast({ title: '订单已创建(支付待接入)', icon: 'none' })
				}).catch(function() {})
			},
			buyVip: function(plan) {
				var self = this
				shopApi.createVipOrder(plan.id).then(function() {
					uni.showToast({ title: '订单已创建(支付待接入)', icon: 'none' })
				}).catch(function() {})
			}
		}
	}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f7f7fa; }
.page-header { padding: 20rpx 8rpx 28rpx; }
.page-title { font-size: 44rpx; font-weight: 800; color: #1e1b4b; display: block; }
.page-desc { font-size: 26rpx; color: #94a3b8; display: block; margin-top: 8rpx; }
.section { margin-top: 12rpx; }
.section-head { margin-bottom: 20rpx; }
.section-title { font-size: 32rpx; font-weight: 700; color: #1e1b4b; }
.packages { display: flex; flex-wrap: wrap; gap: 20rpx; }
.pkg-card { width: calc(50% - 10rpx); background: #fff; border-radius: 24rpx; padding: 36rpx 24rpx; text-align: center; position: relative; border: 3rpx solid #e2e8f0; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04); overflow: hidden; }
.pkg-card:active { transform: scale(0.96); }
.pkg-card.popular { border-color: #4F46E5; background: linear-gradient(180deg, #EEF2FF 0%, #fff 30%); box-shadow: 0 8rpx 32rpx rgba(79,70,229,0.15); }
.pkg-badge { position: absolute; top: 0; right: 0; background: linear-gradient(135deg, #F59E0B, #D97706); color: #fff; font-size: 20rpx; padding: 6rpx 20rpx; border-radius: 0 20rpx 0 16rpx; font-weight: 700; }
.pkg-name { font-size: 28rpx; color: #374151; font-weight: 600; display: block; }
.pkg-points { display: block; font-size: 24rpx; color: #64748b; margin: 12rpx 0; }
.pkg-price-row { display: flex; align-items: baseline; justify-content: center; }
.pkg-price { font-size: 48rpx; font-weight: 800; color: #F59E0B; }
.pkg-yuan { font-size: 24rpx; color: #F59E0B; font-weight: 600; margin-left: 4rpx; }
.pkg-original { font-size: 22rpx; color: #d1d5db; text-decoration: line-through; }
.plan-card { background: #fff; border-radius: 24rpx; padding: 36rpx; margin-bottom: 20rpx; border: 3rpx solid #e2e8f0; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04); }
.plan-card:active { transform: scale(0.98); }
.plan-top { display: flex; justify-content: space-between; align-items: center; }
.plan-name { font-size: 32rpx; font-weight: 700; color: #1e1b4b; }
.plan-price-wrap { display: flex; align-items: baseline; }
.plan-price { font-size: 48rpx; font-weight: 800; color: #4F46E5; }
.plan-yuan { font-size: 24rpx; color: #4F46E5; font-weight: 600; margin-left: 4rpx; }
.plan-original { font-size: 24rpx; color: #d1d5db; text-decoration: line-through; display: block; margin-top: 8rpx; }
.plan-features { margin-top: 20rpx; padding-top: 20rpx; border-top: 2rpx solid #f1f5f9; }
.plan-feature { display: flex; align-items: center; gap: 12rpx; margin-top: 12rpx; }
.feature-check { font-size: 28rpx; color: #10B981; font-weight: 700; width: 32rpx; }
.feature-text { font-size: 26rpx; color: #475569; }
</style>