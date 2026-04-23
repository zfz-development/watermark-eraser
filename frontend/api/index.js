const BASE_URL = '/api/v1'

function getToken() {
  return uni.getStorageSync('token') || ''
}

function request(options) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const header = {
      'Content-Type': 'application/json',
      ...(options.header || {})
    }
    if (token) {
      header['Authorization'] = 'Bearer ' + token
    }
    uni.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: header,
      success(res) {
        if (res.statusCode === 401) {
          uni.removeStorageSync('token')
          uni.removeStorageSync('userInfo')
          uni.showToast({ title: '璇烽噸鏂扮櫥褰?, icon: 'none' })
          setTimeout(() => uni.navigateTo({ url: '/pages/login/index' }), 1500)
          reject(new Error('鏈櫥褰?))
          return
        }
        const body = res.data
        if (body.code !== 0) {
          uni.showToast({ title: body.message || '璇锋眰澶辫触', icon: 'none' })
          reject(new Error(body.message))
          return
        }
        resolve(body.data)
      },
      fail(err) {
        uni.showToast({ title: '缃戠粶閿欒', icon: 'none' })
        reject(err)
      }
    })
  })
}

function uploadFile(filePath) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    uni.uploadFile({
      url: BASE_URL + '/upload',
      filePath: filePath,
      name: 'file',
      header: token ? { Authorization: 'Bearer ' + token } : {},
      success(res) {
        const body = JSON.parse(res.data)
        if (body.code !== 0) {
          uni.showToast({ title: body.message, icon: 'none' })
          reject(new Error(body.message))
          return
        }
        resolve(body.data)
      },
      fail(err) {
        uni.showToast({ title: '涓婁紶澶辫触', icon: 'none' })
        reject(err)
      }
    })
  })
}

function downloadFile(url) {
  return new Promise((resolve, reject) => {
    const token = getToken()
    const fullUrl = url.startsWith('http') ? url : url
    uni.downloadFile({
      url: fullUrl,
      header: token ? { Authorization: 'Bearer ' + token } : {},
      success(res) {
        if (res.statusCode === 200) {
          resolve(res.tempFilePath)
        } else {
          reject(new Error('涓嬭浇澶辫触'))
        }
      },
      fail: reject
    })
  })
}

export { request, uploadFile, downloadFile }
export default request
