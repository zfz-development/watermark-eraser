const ALLOWED_IMAGES = ['jpg', 'jpeg', 'png', 'webp']
const ALLOWED_VIDEOS = ['mp4', 'mov', 'avi']
const MAX_IMAGE_SIZE = 30 * 1024 * 1024
const MAX_VIDEO_SIZE = 500 * 1024 * 1024

export function getFileExt(name) {
  return (name.split('.').pop() || '').toLowerCase()
}

export function isImage(name) {
  return ALLOWED_IMAGES.includes(getFileExt(name))
}

export function isVideo(name) {
  return ALLOWED_VIDEOS.includes(getFileExt(name))
}

export function isAllowedFile(name) {
  return isImage(name) || isVideo(name)
}

export function formatSize(bytes) {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1024 / 1024).toFixed(1) + 'MB'
}
