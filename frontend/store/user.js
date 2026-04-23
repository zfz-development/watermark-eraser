import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: uni.getStorageSync('token') || '',
    userInfo: JSON.parse(uni.getStorageSync('userInfo') || 'null'),
    isLoggedIn: !!uni.getStorageSync('token')
  }),
  actions: {
    setLogin(token, user) {
      this.token = token
      this.userInfo = user
      this.isLoggedIn = true
      uni.setStorageSync('token', token)
      uni.setStorageSync('userInfo', JSON.stringify(user))
    },
    setUser(user) {
      this.userInfo = user
      uni.setStorageSync('userInfo', JSON.stringify(user))
    },
    logout() {
      this.token = ''
      this.userInfo = null
      this.isLoggedIn = false
      uni.removeStorageSync('token')
      uni.removeStorageSync('userInfo')
    }
  }
})
