import request from './request'

export const getNavTree = () => request.get('/knowledge/nav')
export const createNavNode = (data) => request.post('/knowledge/nav', data)
export const updateNavNode = (id, data) => request.put(`/knowledge/nav/${id}`, data)
export const deleteNavNode = (id) => request.delete(`/knowledge/nav/${id}`)
export const linkContent = (nodeId, contentType, contentId) =>
  request.post(`/knowledge/nav/${nodeId}/link`, null, { params: { content_type: contentType, content_id: contentId } })
