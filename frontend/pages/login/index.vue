<template>
	<view class="container">
		<view class="deco deco-1"></view>
		<view class="deco deco-2"></view>
		<view class="brand">
			<view class="brand-logo">
				<image src="/static/logo.png" mode="aspectFit" style="width:80rpx;height:80rpx;"></image>
			</view>
			<text class="brand-text">WATERMARK ERASER</text>
		</view>
		<view class="card">
			<text class="card-title">{{ isRegister ? '创建账号' : '欢迎回来' }}</text>
			<text class="card-sub">{{ isRegister ? '注册即可免费领取积分' : '登录以继续使用服务' }}</text>
			<view class="input-group">
				<text class="input-label">手机号</text>
				<view class="input-wrap">
					<text class="input-prefix">+86</text>
					<input class="input-field" type="number" v-model="phone" placeholder="请输入手机号" maxlength="11" />
				</view>
			</view>
			<view class="input-group">
				<text class="input-label">验证码</text>
				<view class="input-wrap">
					<input class="input-field" type="number" v-model="code" placeholder="请输入验证码" maxlength="6" />
					<button class="sms-btn" @tap="sendSms" :disabled="smsCooldown > 0">{{ smsBtnText }}</button>
				</view>
			</view>
			<view class="input-group" v-if="isRegister">
				<text class="input-label">邀请码（选填）</text>
				<view class="input-wrap">
					<input class="input-field" v-model="inviteCode" placeholder="有邀请码可额外获赠积分" />
				</view>
			</view>
			<button class="submit-btn" @tap="submit">{{ isRegister ? '立即注册' : '登录' }}</button>
			<text class="switch-link" @tap="toggleMode">{{ isRegister ? '已有账号？立即登录' : '没有账号？免费注册' }}</text>
		</view>
		<text class="footer-text">登录即表示同意《用户协议》和《隐私政策》</text>
	</view>
</template>

<script>
	import * as api from '../../api/user.js'
	import * as userStore from '../../store/user.js'

	export default {
		data: function() {
			return {
				phone: '',
				code: '',
				inviteCode: '',
				isRegister: false,
				smsCooldown: 0,
				timer: null
			}
		},
		computed: {
			smsBtnText: function() {
				return this.smsCooldown > 0 ? this.smsCooldown + 's' : '获取验证码'
			}
		},
		onUnload: function() {
			if (this.timer) clearInterval(this.timer)
		},
		methods: {
			toggleMode: function() {
				this.isRegister = !this.isRegister
			},
			sendSms: function() {
				if (this.phone.length !== 11) {
					uni.showToast({ title: '请输入正确手机号', icon: 'none' })
					return
				}
				var self = this
				api.sendSms(this.phone).then(function() {
					self.smsCooldown = 60
					self.timer = setInterval(function() {
						self.smsCooldown--
						if (self.smsCooldown <= 0) clearInterval(self.timer)
					}, 1000)
					uni.showToast({ title: '验证码已发送（测试:888888）', icon: 'none' })
				})
			},
			submit: function() {
				if (this.phone.length !== 11 || this.code.length < 4) {
					uni.showToast({ title: '请填写完整', icon: 'none' })
					return
				}
				var self = this
				var p
				if (this.isRegister) {
					p = api.register(this.phone, this.code, this.inviteCode || undefined)
				} else {
					p = api.login(this.phone, this.code)
				}
				p.then(function(res) {
					userStore.useUserStore().setLogin(res.token, res.user)
					uni.showToast({ title: self.isRegister ? '注册成功' : '登录成功', icon: 'success' })
					setTimeout(function() { uni.navigateBack() }, 1000)
				})
			}
		}
	}
</script>

<style scoped>
.container { min-height: 100vh; background: linear-gradient(160deg, #4F46E5 0%, #7C3AED 50%, #6366F1 100%); position: relative; overflow: hidden; }
.deco { position: absolute; border-radius: 50%; opacity: 0.08; background: #fff; }
.deco-1 { width: 400rpx; height: 400rpx; top: -120rpx; right: -100rpx; }
.deco-2 { width: 250rpx; height: 250rpx; bottom: 100rpx; left: -80rpx; }
.brand { text-align: center; padding: 100rpx 0 48rpx; position: relative; z-index: 1; }
.brand-logo { width: 120rpx; height: 120rpx; margin: 0 auto 20rpx; background: rgba(255,255,255,0.2); border-radius: 28rpx; display: flex; align-items: center; justify-content: center; }
.brand-text { font-size: 28rpx; color: rgba(255,255,255,0.7); font-weight: 600; letter-spacing: 4rpx; }
.card { margin: 0 48rpx; background: #fff; border-radius: 36rpx; padding: 56rpx 44rpx 48rpx; box-shadow: 0 24rpx 64rpx rgba(0,0,0,0.15); position: relative; z-index: 1; }
.card-title { font-size: 44rpx; font-weight: 800; color: #1e1b4b; display: block; }
.card-sub { font-size: 26rpx; color: #94a3b8; display: block; margin-top: 8rpx; margin-bottom: 40rpx; }
.input-group { margin-bottom: 28rpx; }
.input-label { font-size: 26rpx; font-weight: 600; color: #475569; display: block; margin-bottom: 12rpx; }
.input-wrap { display: flex; align-items: center; border: 2rpx solid #e2e8f0; border-radius: 20rpx; padding: 0 24rpx; background: #f8fafc; height: 96rpx; }
.input-prefix { font-size: 30rpx; font-weight: 600; color: #1e293b; margin-right: 16rpx; padding-right: 16rpx; border-right: 2rpx solid #e2e8f0; }
.input-field { flex: 1; font-size: 30rpx; color: #1e293b; height: 96rpx; }
.sms-btn { background: linear-gradient(135deg, #6366F1, #4F46E5); color: #fff; border-radius: 16rpx; font-size: 24rpx; min-height: 68rpx; line-height: 68rpx; padding: 0 24rpx; white-space: nowrap; font-weight: 600; }
.sms-btn[disabled] { background: #e2e8f0; color: #94a3b8; }
.submit-btn { margin-top: 40rpx; background: linear-gradient(135deg, #4F46E5, #7C3AED); color: #fff; border-radius: 50rpx; height: 100rpx; line-height: 100rpx; font-size: 34rpx; font-weight: 700; box-shadow: 0 12rpx 36rpx rgba(79,70,229,0.4); letter-spacing: 4rpx; }
.submit-btn:active { transform: scale(0.97); }
.switch-link { display: block; text-align: center; margin-top: 36rpx; font-size: 28rpx; color: #6366F1; font-weight: 600; }
.footer-text { display: block; text-align: center; margin-top: 48rpx; font-size: 22rpx; color: rgba(255,255,255,0.4); position: relative; z-index: 1; }
</style>