import request from './request'

export const getTags = () => {
  return request.get('/api/tags/')
}

export const getTagTree = () => {
  return request.get('/api/tags/tree')
}

export const createTag = (data) => {
  return request.post('/api/tags/', data)
}

export const updateTag = (tagId, data) => {
  return request.put(`/api/tags/${tagId}`, data)
}

export const deleteTag = (tagId) => {
  return request.delete(`/api/tags/${tagId}`)
}

export const addTagToPage = (pageId, tagId) => {
  return request.post(`/api/tags/pages/${pageId}/tags/${tagId}`)
}

export const removeTagFromPage = (pageId, tagId) => {
  return request.delete(`/api/tags/pages/${pageId}/tags/${tagId}`)
}