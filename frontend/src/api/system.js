import request from './request'

// 系统状态
export const getSystemStatus = () => request.get('/system/status')

// 配置 Schema
export const getConfigSchema = () => request.get('/system/config/schema')

// 配置 CRUD
export const getAllConfigs = () => request.get('/system/config')
export const getCategoryConfig = (category) => request.get(`/system/config/${category}`)
export const updateCategoryConfig = (category, configs) =>
  request.put(`/system/config/${category}`, { configs })

// 连接测试
export const testConnection = (type, configs) =>
  request.post(`/system/test/${type}`, { configs })

// LLM 提供商
export const getLLMProviders = () => request.get('/system/llm/providers')
export const getProviderModels = (name) => request.get(`/system/llm/providers/${name}/models`)
export const getProviderDefaultConfig = (name) =>
  request.get(`/system/llm/providers/${name}/default-config`)
export const fetchModelsFromAPI = (provider, api_key, api_base) =>
  request.post('/system/llm/fetch-models', { provider, api_key, api_base })

// 系统初始化
export const initSystem = (data) => request.post('/system/init', data)
