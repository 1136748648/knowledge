import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail || error.response?.data?.message
    
    let message = detail || error.message || '请求失败'
    
    if (status === 401) {
      localStorage.removeItem('token')
      ElMessage.warning('登录已过期，请重新登录')
      setTimeout(() => {
        window.location.href = '/login'
      }, 1500)
    } else if (status === 403) {
      message = detail || '您没有权限执行此操作'
      ElMessage.warning(message)
    } else if (status === 404) {
      message = detail || '资源未找到'
      ElMessage.error(message)
    } else if (status === 500) {
      message = '服务器内部错误，请稍后重试'
      ElMessage.error(message)
    } else {
      ElMessage.error(message)
    }
    
    return Promise.reject(error)
  }
)

export default request
