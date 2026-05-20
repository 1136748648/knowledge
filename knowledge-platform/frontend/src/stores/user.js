import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/api/request'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => userInfo.value?.roles?.includes('admin'))

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  async function fetchUserInfo() {
    try {
      const data = await request.get('/auth/me')
      userInfo.value = data
    } catch (e) {
      // Token invalid, clear
      logout()
    }
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  return { token, userInfo, isLoggedIn, isAdmin, setToken, fetchUserInfo, logout }
})
