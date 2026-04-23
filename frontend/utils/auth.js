export function getToken() {
  return uni.getStorageSync('token') || ''
}

export function setToken(t) {
  uni.setStorageSync('token', t)
}

export function removeToken() {
  uni.removeStorageSync('token')
}

export function isLoggedIn() {
  return !!getToken()
}

export function requireAuth() {
  if (!isLoggedIn()) {
    uni.navigateTo({ url: '/pages/login/index' })
    return false
  }
  return true
}
