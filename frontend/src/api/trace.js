import request from './request'

export const traceApi = {
  listTraces(params) {
    return request.get('/api/trace/list', { params })
  },

  getTraceDetail(traceId) {
    return request.get(`/api/trace/${traceId}`)
  },

  getTraceSummary(traceId) {
    return request.get(`/api/trace/${traceId}/summary`)
  },

  getUserStats(params) {
    return request.get('/api/trace/stats/user', { params })
  },

  getTeamStats(params) {
    return request.get('/api/trace/stats/team', { params })
  }
}
