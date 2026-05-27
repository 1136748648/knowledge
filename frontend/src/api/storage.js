import request from './request'

export const getUploadUrl = (filePath, expiresIn = 900) => {
  return request.post('/storage/upload-url', { file_path: filePath, expires_in: expiresIn })
}

export const processDocument = (pageId, filePath) => {
  return request.post('/storage/process-document', { page_id: pageId, file_path: filePath })
}

export const getProcessStatus = (pageId) => {
  return request.get(`/storage/process-status/${pageId}`)
}

export const testStorageConnection = () => {
  return request.post('/storage/test')
}

