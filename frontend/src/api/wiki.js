import request from './request'

export const getWikiPages = (params) => request.get('/wiki/', { params })
export const getWikiPage = (id) => request.get(`/wiki/${id}`)
export const createWikiPage = (data) => request.post('/wiki/', data)
export const updateWikiPage = (id, data) => request.put(`/wiki/${id}`, data)
export const deleteWikiPage = (id) => request.delete(`/wiki/${id}`)
export const searchWiki = (query) => request.get(`/wiki/search/${query}`)
export const getUploadUrl = (filename) => request.get(`/storage/upload-url/${filename}`)
export const uploadFile = (url, file) => {
  const formData = new FormData()
  formData.append('file', file)
  return fetch(url, { method: 'PUT', body: formData })
}
export const processDocument = (pageId, fileId) => request.post('/storage/process-document', { page_id: pageId, file_id: fileId })
export const getProcessStatus = (pageId) => request.get(`/storage/process-status/${pageId}`)
