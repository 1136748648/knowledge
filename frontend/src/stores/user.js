import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/api/request'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref({
    user_id: '',
    username: '',
    email: '',
    roles: [],
    dept_id: null,
    clearance_level: 1,
  })

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.roles?.includes('admin'))
  const hasRole = computed((role) => userInfo.value?.roles?.includes(role))

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  async function fetchUserInfo() {
    try {
      const data = await request.get('/auth/me')
      userInfo.value = {
        user_id: data.user_id || '',
        username: data.username || '',
        email: data.email || '',
        roles: data.roles || [],
        dept_id: data.dept_id || null,
        clearance_level: data.clearance_level || 1,
      }
    } catch (e) {
      logout()
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = {
      user_id: '',
      username: '',
      email: '',
      roles: [],
      dept_id: null,
      clearance_level: 1,
    }
    localStorage.removeItem('token')
  }

  return { token, userInfo, isLoggedIn, isAdmin, hasRole, setToken, fetchUserInfo, logout }
})
