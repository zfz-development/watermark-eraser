import request from './index'

export function signIn() {
  return request({ url: '/user/sign-in', method: 'POST' })
}

export function invite(inviteCode) {
  return request({ url: '/user/invite', method: 'POST', data: { invite_code: inviteCode } })
}

export function getPointsLogs(params) {
  return request({ url: '/user/points/logs', data: params })
}
