import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token'))
  const isLoggedIn = computed(() => !!token.value && !!user.value)

  async function login(email, password) {
    const res = await authApi.login(email, password)
    token.value = res.data.access_token
    localStorage.setItem('token', token.value)
    await fetchMe()
  }

  async function register(data) {
    await authApi.register(data)
    await login(data.email, data.password)
  }

  async function fetchMe() {
    try {
      const res = await authApi.me()
      user.value = res.data
    } catch {
      logout()
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
  }

  return { user, token, isLoggedIn, login, register, fetchMe, logout }
})
