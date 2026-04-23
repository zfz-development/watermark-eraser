import request, { uploadFile, downloadFile } from './index'

export { uploadFile }

export function removeWatermark(fileId, mask, quality) {
  return request({ url: '/watermark/remove', method: 'POST', data: { file_id: fileId, mask, quality } })
}

export function getTask(taskId) {
  return request({ url: '/task/' + taskId })
}

export function getTasks(params) {
  return request({ url: '/tasks', data: params })
}

export function deleteTask(taskId) {
  return request({ url: '/task/' + taskId, method: 'DELETE' })
}

export function downloadResult(fileId) {
  return downloadFile('/api/v1/download/' + fileId)
}
