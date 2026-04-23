import request from './index'

export function sendSms(phone) {
  return request({ url: '/user/sms/send', method: 'POST', data: { phone } })
}

export function register(phone, code, inviteCode) {
  return request({ url: '/user/register', method: 'POST', data: { phone, code, invite_code: inviteCode } })
}

export function login(phone, code) {
  return request({ url: '/user/login', method: 'POST', data: { phone, code } })
}

export function getProfile() {
  return request({ url: '/user/profile' })
}

export function updateProfile(data) {
  return request({ url: '/user/profile', method: 'PUT', data })
}
