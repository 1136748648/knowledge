import request from './request'

export const getUploadUrl = (filePath, expiresIn = 900) => {
  return request.post('/api/storage/upload-url', { file_path: filePath, expires_in: expiresIn })
}

export const getDownloadUrl = (fileId, filePath, expiresIn = 300) => {
  return request.get(`/api/storage/download-url/${fileId}`, { params: { file_path: filePath, expires_in: expiresIn } })
}

export const testStorageConnection = () => {
  return request.post('/api/storage/test')
}

export const getStorageStatus = () => {
  return request.get('/api/storage/status')
}