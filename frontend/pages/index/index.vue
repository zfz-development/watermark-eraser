<template>
	<view class="container">
		<view class="hero">
			<view class="hero-deco hero-deco-1"></view>
			<view class="hero-deco hero-deco-2"></view>
			<view class="hero-content">
				<view class="logo-wrap">
					<image class="logo" src="/static/logo.png" mode="aspectFit"></image>
				</view>
				<text class="hero-title">一键去除水印</text>
				<text class="hero-sub">AI 智能识别 · 高质量修复 · 极速处理</text>
			</view>
		</view>
		<view class="entries">
			<view class="entry-card" @tap="goUpload">
				<view class="entry-icon-wrap">
					<text class="entry-emoji">&#x1F5BC;</text>
				</view>
				<view class="entry-info">
					<text class="entry-title">图片去水印</text>
					<text class="entry-desc">JPG / PNG / WEBP</text>
				</view>
				<text class="entry-arrow">&#x276F;</text>
			</view>
			<view class="entry-card" @tap="goUpload">
				<view class="entry-icon-wrap entry-icon-purple">
					<text class="entry-emoji">&#x1F3AC;</text>
				</view>
				<view class="entry-info">
					<text class="entry-title">视频去水印</text>
					<text class="entry-desc">MP4 / MOV / AVI</text>
				</view>
				<text class="entry-arrow">&#x276F;</text>
			</view>
		</view>
		<view class="quick-row">
			<view class="quick-item" @tap="goPage('/pages/sign-in/index')">
				<text class="quick-icon">&#x1F4C5;</text>
				<text class="quick-label">每日签到</text>
			</view>
			<view class="quick-divider"></view>
			<view class="quick-item" @tap="goPage('/pages/shop/index')">
				<text class="quick-icon">&#x1F4B0;</text>
				<text class="quick-label">积分商城</text>
			</view>
			<view class="quick-divider"></view>
			<view class="quick-item" @tap="goPage('/pages/vip/index')">
				<text class="quick-icon">&#x1F451;</text>
				<text class="quick-label">VIP 会员</text>
			</view>
		</view>
		<view class="stats-banner">
			<view class="stats-item">
				<text class="stats-num">AI</text>
				<text class="stats-label">智能识别</text>
			</view>
			<view class="stats-sep"></view>
			<view class="stats-item">
				<text class="stats-num">HD</text>
				<text class="stats-label">高清输出</text>
			</view>
			<view class="stats-sep"></view>
			<view class="stats-item">
				<text class="stats-num">99%</text>
				<text class="stats-label">满意度</text>
			</view>
		</view>
	</view>
</template>

<script>
	export default {
		methods: {
			goUpload: function() {
				uni.switchTab({ url: '/pages/upload/index' })
			},
			goPage: function(url) {
				uni.navigateTo({ url: url })
			}
		}
	}
</script>

<style scoped>
.container { min-height: 100vh; background: #f7f7fa; padding-bottom: 60rpx; }
.hero { position: relative; padding: 120rpx 40rpx 100rpx; background: linear-gradient(145deg, #4F46E5 0%, #7C3AED 60%, #6366F1 100%); border-radius: 0 0 48rpx 48rpx; overflow: hidden; }
.hero-deco { position: absolute; border-radius: 50%; opacity: 0.12; }
.hero-deco-1 { width: 300rpx; height: 300rpx; background: #fff; top: -80rpx; right: -60rpx; }
.hero-deco-2 { width: 200rpx; height: 200rpx; background: #F59E0B; bottom: -40rpx; left: -40rpx; }
.hero-content { position: relative; text-align: center; z-index: 1; }
.logo-wrap { width: 160rpx; height: 160rpx; margin: 0 auto 32rpx; background: rgba(255,255,255,0.2); border-radius: 40rpx; display: flex; align-items: center; justify-content: center; }
.logo { width: 120rpx; height: 120rpx; }
.hero-title { display: block; font-size: 52rpx; font-weight: 800; color: #fff; letter-spacing: 4rpx; text-shadow: 0 4rpx 16rpx rgba(0,0,0,0.15); }
.hero-sub { display: block; font-size: 26rpx; color: rgba(255,255,255,0.75); margin-top: 16rpx; font-weight: 500; letter-spacing: 2rpx; }
.entries { padding: 0 32rpx; margin-top: -48rpx; position: relative; z-index: 2; }
.entry-card { display: flex; align-items: center; background: #fff; border-radius: 28rpx; padding: 36rpx 32rpx; margin-bottom: 20rpx; box-shadow: 0 8rpx 40rpx rgba(0,0,0,0.08); }
.entry-card:active { transform: scale(0.97); }
.entry-icon-wrap { width: 96rpx; height: 96rpx; border-radius: 24rpx; background: linear-gradient(135deg, #EEF2FF, #E0E7FF); display: flex; align-items: center; justify-content: center; }
.entry-icon-purple { background: linear-gradient(135deg, #F5F3FF, #EDE9FE); }
.entry-emoji { font-size: 48rpx; }
.entry-info { flex: 1; margin-left: 28rpx; }
.entry-title { display: block; font-size: 32rpx; font-weight: 700; color: #1e1b4b; }
.entry-desc { display: block; font-size: 24rpx; color: #94a3b8; margin-top: 6rpx; }
.entry-arrow { font-size: 28rpx; color: #cbd5e1; }
.quick-row { display: flex; align-items: center; margin: 32rpx 32rpx 0; background: #fff; border-radius: 24rpx; padding: 16rpx 0; box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.04); }
.quick-item { flex: 1; text-align: center; padding: 20rpx 0; }
.quick-icon { font-size: 40rpx; display: block; text-align: center; }
.quick-label { display: block; font-size: 24rpx; color: #64748b; margin-top: 8rpx; font-weight: 500; text-align: center; }
.quick-divider { width: 2rpx; height: 48rpx; background: #f1f5f9; }
.stats-banner { display: flex; margin: 32rpx 32rpx 0; background: linear-gradient(135deg, #4F46E5, #6366F1); border-radius: 24rpx; padding: 36rpx 0; box-shadow: 0 8rpx 32rpx rgba(79,70,229,0.25); }
.stats-item { flex: 1; text-align: center; }
.stats-num { display: block; font-size: 36rpx; font-weight: 800; color: #F59E0B; text-align: center; }
.stats-label { display: block; font-size: 22rpx; color: rgba(255,255,255,0.7); margin-top: 4rpx; text-align: center; }
.stats-sep { width: 2rpx; height: 48rpx; background: rgba(255,255,255,0.15); align-self: center; }
</style>