import request from './index'

export function getPackages() {
  return request({ url: '/shop/packages' })
}

export function getVipPlans() {
  return request({ url: '/shop/vip-plans' })
}

export function createPointOrder(packageId) {
  return request({ url: '/shop/order/points', method: 'POST', data: { package_id: packageId } })
}

export function createVipOrder(planId) {
  return request({ url: '/shop/order/vip', method: 'POST', data: { plan_id: planId } })
}
