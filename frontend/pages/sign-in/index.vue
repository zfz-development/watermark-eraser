<template>
	<view class="container">
		<view class="hero-mini">
			<text class="hero-mini-emoji">&#x1F4C5;</text>
			<text class="hero-mini-title">每日签到</text>
			<text class="hero-mini-sub">坚持签到，积分不断</text>
		</view>
		<view class="sign-card">
			<view class="streak-section">
				<text class="streak-num">{{ days }}</text>
				<text class="streak-unit">天连续签到</text>
			</view>
			<button :class="['sign-btn', signed?'signed':'']" @tap="doSignIn" :disabled="signed">
				<text class="sign-btn-icon" v-if="!signed">&#x2B50;</text>
				<text>{{ signed ? '今日已签到' : '立即签到' }}</text>
			</button>
			<text class="sign-hint" v-if="!signed">签到即可获得积分奖励</text>
		</view>
		<view class="rules-card">
			<text class="rules-title">&#x1F4DD; 签到奖励规则</text>
			<view class="rule-item">
				<view class="rule-dot rule-dot-1"></view>
				<text class="rule-text">每日签到 +1 积分</text>
			</view>
			<view class="rule-item">
				<view class="rule-dot rule-dot-2"></view>
				<text class="rule-text">连续 7 天额外 +3 积分</text>
			</view>
			<view class="rule-item">
				<view class="rule-dot rule-dot-3"></view>
				<text class="rule-text">连续 30 天额外 +10 积分</text>
			</view>
		</view>
	</view>
</template>

<script>
	import * as pointsApi from '../../api/points.js'
	import * as userApi from '../../api/user.js'
	import * as authUtils from '../../utils/auth.js'

	export default {
		data: function() {
			return {
				signed: false,
				days: 0
			}
		},
		onShow: function() {
			if (!authUtils.isLoggedIn()) {
				uni.navigateTo({ url: '/pages/login/index' })
				return
			}
			var self = this
			userApi.getProfile().then(function(p) {
				self.signed = p.today_sign_in
			}).catch(function() {})
		},
		methods: {
			doSignIn: function() {
				if (this.signed) return
				var self = this
				pointsApi.signIn().then(function(res) {
					self.signed = true
					self.days = res.consecutive_days
					uni.showToast({ title: '签到成功！+' + res.reward_points + '积分', icon: 'success' })
				}).catch(function() {})
			}
		}
	}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f7f7fa; }
.hero-mini { text-align: center; padding: 40rpx 0 32rpx; }
.hero-mini-emoji { font-size: 56rpx; display: block; margin-bottom: 12rpx; }
.hero-mini-title { font-size: 44rpx; font-weight: 800; color: #1e1b4b; display: block; }
.hero-mini-sub { font-size: 26rpx; color: #94a3b8; display: block; margin-top: 8rpx; }
.sign-card { background: #fff; border-radius: 32rpx; padding: 56rpx 40rpx; text-align: center; box-shadow: 0 8rpx 40rpx rgba(0,0,0,0.07); }
.streak-section { display: flex; align-items: baseline; justify-content: center; gap: 8rpx; margin-bottom: 8rpx; }
.streak-num { font-size: 72rpx; font-weight: 800; color: #4F46E5; }
.streak-unit { font-size: 28rpx; color: #6366F1; font-weight: 600; }
.sign-btn { margin-top: 40rpx; background: linear-gradient(135deg, #4F46E5, #7C3AED); color: #fff; border-radius: 50rpx; height: 100rpx; line-height: 100rpx; font-size: 34rpx; font-weight: 700; box-shadow: 0 12rpx 36rpx rgba(79,70,229,0.4); letter-spacing: 2rpx; }
.sign-btn:active { transform: scale(0.96); }
.sign-btn.signed { background: linear-gradient(135deg, #e2e8f0, #cbd5e1); box-shadow: none; color: #94a3b8; }
.sign-btn-icon { font-size: 32rpx; margin-right: 8rpx; }
.sign-hint { display: block; font-size: 24rpx; color: #94a3b8; margin-top: 20rpx; }
.rules-card { background: #fff; border-radius: 28rpx; padding: 40rpx; margin-top: 24rpx; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04); }
.rules-title { font-size: 30rpx; font-weight: 700; color: #1e1b4b; display: block; margin-bottom: 28rpx; }
.rule-item { display: flex; align-items: center; gap: 16rpx; margin-bottom: 20rpx; }
.rule-item:last-child { margin-bottom: 0; }
.rule-dot { width: 16rpx; height: 16rpx; border-radius: 50%; }
.rule-dot-1 { background: #4F46E5; }
.rule-dot-2 { background: #F59E0B; }
.rule-dot-3 { background: #10B981; }
.rule-text { font-size: 28rpx; color: #475569; }
</style>