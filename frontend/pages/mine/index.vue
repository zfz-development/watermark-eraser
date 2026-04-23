<template>
	<view class="container">
		<view class="top-bg">
			<view class="top-deco"></view>
		</view>
		<view class="profile-card">
			<view class="avatar">{{ avatarText }}</view>
			<view class="user-info">
				<text class="nickname">{{ nickname }}</text>
				<text class="phone">{{ phone }}</text>
			</view>
			<view class="points-badge">
				<text class="points-num">{{ points }}</text>
				<text class="points-label">积分</text>
			</view>
		</view>
		<view class="vip-banner" v-if="isVip">
			<text class="vip-icon">&#x1F451;</text>
			<text class="vip-text">VIP 会员生效中</text>
			<text class="vip-go" @tap="goPage('/pages/vip/index')">查看权益 ></text>
		</view>
		<view class="menu-group">
			<view class="menu-card">
				<view class="menu-item" @tap="goPage('/pages/sign-in/index')">
					<view class="menu-icon-wrap menu-icon-blue">
						<text class="menu-icon-text">&#x1F4C5;</text>
					</view>
					<text class="menu-label">每日签到</text>
					<text class="menu-arrow">&#x276F;</text>
				</view>
				<view class="menu-item" @tap="goPage('/pages/shop/index')">
					<view class="menu-icon-wrap menu-icon-gold">
						<text class="menu-icon-text">&#x1F4B0;</text>
					</view>
					<text class="menu-label">购买积分</text>
					<text class="menu-arrow">&#x276F;</text>
				</view>
				<view class="menu-item" @tap="goPage('/pages/vip/index')">
					<view class="menu-icon-wrap menu-icon-purple">
						<text class="menu-icon-text">&#x1F451;</text>
					</view>
					<text class="menu-label">开通 VIP</text>
					<text class="menu-arrow">&#x276F;</text>
				</view>
				<view class="menu-item" @tap="goTab('/pages/history/index')">
					<view class="menu-icon-wrap menu-icon-green">
						<text class="menu-icon-text">&#x1F4CB;</text>
					</view>
					<text class="menu-label">历史记录</text>
					<text class="menu-arrow">&#x276F;</text>
				</view>
			</view>
		</view>
		<view class="invite-section" v-if="inviteCode">
			<text class="invite-title">&#x1F310; 我的邀请码</text>
			<view class="invite-code" @tap="copyCode">
				<text>{{ inviteCode }}</text>
			</view>
			<text class="invite-hint">邀请好友注册，双方各得 3 积分</text>
		</view>
		<button v-if="!isLoggedIn" class="login-btn" @tap="goPage('/pages/login/index')">登录 / 注册</button>
		<button v-else class="logout-btn" @tap="logout">退出登录</button>
	</view>
</template>

<script>
	import * as userApi from '../../api/user.js'
	import * as userStore from '../../store/user.js'
	import * as authUtils from '../../utils/auth.js'

	export default {
		data: function() {
			return {
				userInfo: null,
				isLoggedIn: false
			}
		},
		computed: {
			nickname: function() { return this.userInfo ? this.userInfo.nickname : '未登录' },
			phone: function() { return this.userInfo ? this.userInfo.phone : '' },
			points: function() { return this.userInfo ? this.userInfo.points : 0 },
			isVip: function() { return this.userInfo && this.userInfo.vip_level > 0 },
			inviteCode: function() { return this.userInfo ? this.userInfo.invite_code : '' },
			avatarText: function() {
				var n = this.nickname
				return n ? n[0] : '?'
			}
		},
		onShow: function() {
			var self = this
			if (authUtils.isLoggedIn()) {
				this.isLoggedIn = true
				userApi.getProfile().then(function(user) {
					self.userInfo = user
					userStore.useUserStore().setUser(user)
				}).catch(function() {
					self.isLoggedIn = false
				})
			} else {
				this.isLoggedIn = false
				this.userInfo = null
			}
		},
		methods: {
			goPage: function(url) { uni.navigateTo({ url: url }) },
			goTab: function(url) { uni.switchTab({ url: url }) },
			copyCode: function() {
				if (!this.inviteCode) return
				uni.setClipboardData({ data: this.inviteCode })
				uni.showToast({ title: '已复制邀请码', icon: 'success' })
			},
			logout: function() {
				userStore.useUserStore().logout()
				this.isLoggedIn = false
				this.userInfo = null
				uni.showToast({ title: '已退出', icon: 'success' })
			}
		}
	}
</script>

<style scoped>
.container { min-height: 100vh; background: #f7f7fa; padding-bottom: 60rpx; }
.top-bg { position: relative; height: 280rpx; background: linear-gradient(145deg, #4F46E5 0%, #7C3AED 60%, #6366F1 100%); border-radius: 0 0 48rpx 48rpx; overflow: hidden; }
.top-deco { position: absolute; width: 240rpx; height: 240rpx; border-radius: 50%; background: rgba(255,255,255,0.08); top: -80rpx; right: -40rpx; }
.profile-card { display: flex; align-items: center; background: #fff; border-radius: 28rpx; padding: 40rpx; margin: -80rpx 32rpx 0; position: relative; z-index: 2; box-shadow: 0 12rpx 48rpx rgba(0,0,0,0.08); }
.avatar { width: 108rpx; height: 108rpx; border-radius: 50%; background: linear-gradient(135deg, #4F46E5, #7C3AED); color: #fff; font-size: 44rpx; display: flex; align-items: center; justify-content: center; font-weight: 700; box-shadow: 0 8rpx 24rpx rgba(79,70,229,0.3); flex-shrink: 0; }
.user-info { flex: 1; margin-left: 28rpx; overflow: hidden; }
.nickname { font-size: 36rpx; font-weight: 700; color: #1e1b4b; display: block; }
.phone { font-size: 26rpx; color: #94a3b8; display: block; margin-top: 4rpx; }
.points-badge { text-align: center; background: linear-gradient(135deg, #FFFBEB, #FEF3C7); border-radius: 20rpx; padding: 16rpx 28rpx; flex-shrink: 0; }
.points-num { display: block; font-size: 36rpx; font-weight: 800; color: #D97706; }
.points-label { font-size: 20rpx; color: #D97706; font-weight: 600; }
.vip-banner { display: flex; align-items: center; background: linear-gradient(135deg, #F59E0B, #B45309); color: #fff; border-radius: 20rpx; padding: 28rpx 32rpx; margin: 24rpx 32rpx 0; font-size: 28rpx; font-weight: 700; box-shadow: 0 8rpx 24rpx rgba(245,158,11,0.3); }
.vip-icon { font-size: 36rpx; margin-right: 12rpx; }
.vip-text { flex: 1; }
.vip-go { font-size: 24rpx; font-weight: 500; opacity: 0.85; }
.menu-group { margin-top: 24rpx; padding: 0 32rpx; }
.menu-card { background: #fff; border-radius: 24rpx; overflow: hidden; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04); }
.menu-item { padding: 32rpx 32rpx; display: flex; align-items: center; border-bottom: 1rpx solid #f8fafc; }
.menu-item:last-child { border-bottom: none; }
.menu-item:active { background: #f8fafc; }
.menu-icon-wrap { width: 72rpx; height: 72rpx; border-radius: 20rpx; display: flex; align-items: center; justify-content: center; margin-right: 24rpx; }
.menu-icon-blue { background: linear-gradient(135deg, #EEF2FF, #E0E7FF); }
.menu-icon-gold { background: linear-gradient(135deg, #FFFBEB, #FEF3C7); }
.menu-icon-purple { background: linear-gradient(135deg, #F5F3FF, #EDE9FE); }
.menu-icon-green { background: linear-gradient(135deg, #D1FAE5, #A7F3D0); }
.menu-icon-text { font-size: 36rpx; }
.menu-label { flex: 1; font-size: 30rpx; color: #374151; font-weight: 500; }
.menu-arrow { font-size: 24rpx; color: #cbd5e1; }
.invite-section { margin: 32rpx 32rpx 0; text-align: center; background: #fff; border-radius: 24rpx; padding: 40rpx; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04); }
.invite-title { font-size: 28rpx; color: #64748b; font-weight: 600; display: block; margin-bottom: 20rpx; }
.invite-code { font-size: 44rpx; font-weight: 800; color: #4F46E5; margin: 20rpx 0; padding: 20rpx 48rpx; background: linear-gradient(135deg, #EEF2FF, #E0E7FF); border-radius: 20rpx; display: inline-block; letter-spacing: 8rpx; }
.invite-hint { font-size: 24rpx; color: #94a3b8; display: block; margin-top: 16rpx; }
.login-btn { margin: 48rpx 32rpx 0; background: linear-gradient(135deg, #4F46E5, #7C3AED); color: #fff; border-radius: 50rpx; height: 96rpx; line-height: 96rpx; font-size: 32rpx; font-weight: 700; box-shadow: 0 8rpx 32rpx rgba(79,70,229,0.35); }
.logout-btn { margin: 48rpx 32rpx 0; background: #fff; color: #94a3b8; border: 2rpx solid #e2e8f0; border-radius: 50rpx; height: 84rpx; line-height: 84rpx; font-size: 28rpx; font-weight: 500; }
</style>