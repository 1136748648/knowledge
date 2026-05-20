import request from './request'

export const getWikiPages = (params) => request.get('/wiki/', { params })
export const getWikiPage = (id) => request.get(`/wiki/${id}`)
export const createWikiPage = (data) => request.post('/wiki/', data)
export const updateWikiPage = (id, data) => request.put(`/wiki/${id}`, data)
export const deleteWikiPage = (id) => request.delete(`/wiki/${id}`)
export const searchWiki = (query) => request.get(`/wiki/search/${query}`)
