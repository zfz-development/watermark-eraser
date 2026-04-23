<template>
	<view class="container">
		<view class="vip-hero">
			<view class="vip-hero-deco"></view>
			<view class="vip-hero-content">
				<text class="vip-emoji">&#x1F451;</text>
				<text class="vip-hero-title">VIP 会员</text>
				<text class="vip-hero-sub">畅享无限去水印，尊享专属权益</text>
			</view>
		</view>
		<view v-for="(plan, index) in plans" :key="plan.id" :class="['vip-card', index===0?'vip-card-first':'']" @tap="buyVip(plan)">
			<view class="vip-card-top">
				<view>
					<text class="vip-plan-name">{{ plan.name }}</text>
					<text v-if="index===0" class="vip-recommend">推荐</text>
				</view>
				<view class="vip-plan-price-wrap">
					<text class="vip-plan-price">{{ plan.price }}</text>
					<text class="vip-plan-unit">元<text v-if="plan.duration===1">/月</text></text>
				</view>
			</view>
			<text v-if="plan.original_price" class="vip-plan-original">原价 {{ plan.original_price }} 元</text>
			<view class="vip-plan-features">
				<view v-for="f in plan.features" :key="f" class="vip-plan-feature">
					<text class="vip-feat-icon">&#x2713;</text>
					<text class="vip-feat-text">{{ f }}</text>
				</view>
			</view>
		</view>
	</view>
</template>

<script>
	import * as shopApi from '../../api/shop.js'

	export default {
		data: function() {
			return { plans: [] }
		},
		onShow: function() {
			var self = this
			shopApi.getVipPlans().then(function(data) { self.plans = data }).catch(function() {})
		},
		methods: {
			buyVip: function(plan) {
				shopApi.createVipOrder(plan.id).then(function() {
					uni.showToast({ title: '订单已创建(支付待接入)', icon: 'none' })
				}).catch(function() {})
			}
		}
	}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f7f7fa; }
.vip-hero { position: relative; background: linear-gradient(135deg, #F59E0B 0%, #D97706 50%, #B45309 100%); border-radius: 28rpx; padding: 56rpx 40rpx; margin-bottom: 32rpx; overflow: hidden; box-shadow: 0 16rpx 48rpx rgba(245,158,11,0.3); }
.vip-hero-deco { position: absolute; width: 200rpx; height: 200rpx; border-radius: 50%; background: rgba(255,255,255,0.1); top: -60rpx; right: -40rpx; }
.vip-hero-content { position: relative; text-align: center; z-index: 1; }
.vip-emoji { font-size: 64rpx; display: block; margin-bottom: 16rpx; }
.vip-hero-title { font-size: 48rpx; font-weight: 800; color: #fff; display: block; text-shadow: 0 2rpx 8rpx rgba(0,0,0,0.1); }
.vip-hero-sub { font-size: 28rpx; color: rgba(255,255,255,0.85); margin-top: 12rpx; display: block; }
.vip-card { background: #fff; border-radius: 24rpx; padding: 36rpx; margin-bottom: 24rpx; border: 3rpx solid #e2e8f0; box-shadow: 0 6rpx 24rpx rgba(0,0,0,0.04); }
.vip-card:active { transform: scale(0.98); }
.vip-card-first { border-color: #F59E0B; background: linear-gradient(180deg, #FFFBEB 0%, #fff 40%); box-shadow: 0 8rpx 32rpx rgba(245,158,11,0.15); }
.vip-card-top { display: flex; justify-content: space-between; align-items: center; }
.vip-plan-name { font-size: 34rpx; font-weight: 700; color: #1e1b4b; }
.vip-recommend { display: inline-block; margin-left: 12rpx; background: linear-gradient(135deg, #F59E0B, #D97706); color: #fff; font-size: 20rpx; font-weight: 700; padding: 4rpx 16rpx; border-radius: 8rpx; vertical-align: middle; }
.vip-plan-price-wrap { display: flex; align-items: baseline; }
.vip-plan-price { font-size: 52rpx; font-weight: 800; color: #F59E0B; }
.vip-plan-unit { font-size: 26rpx; color: #F59E0B; font-weight: 600; margin-left: 4rpx; }
.vip-plan-original { font-size: 24rpx; color: #d1d5db; text-decoration: line-through; display: block; margin-top: 8rpx; }
.vip-plan-features { margin-top: 24rpx; padding-top: 24rpx; border-top: 2rpx solid #f1f5f9; }
.vip-plan-feature { display: flex; align-items: center; gap: 12rpx; margin-top: 12rpx; }
.vip-feat-icon { font-size: 28rpx; color: #10B981; font-weight: 700; width: 36rpx; }
.vip-feat-text { font-size: 28rpx; color: #475569; }
</style>