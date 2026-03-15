import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const token = ref(localStorage.getItem('token'))
  const isLoggedIn = computed(() => !!token.value && !!user.value)

  // Handle OAuth token from URL (?token=xxx after OAuth redirect)
  function consumeOAuthToken() {
    // Read from hash fragment (#token=xxx) — never sent to server in Referer/logs (A02 fix)
    const hash = window.location.hash
    if (hash.startsWith('#token=')) {
      const t = hash.slice(7)
      token.value = t
      localStorage.setItem('token', t)
      // Strip fragment so token doesn't persist in browser history
      window.history.replaceState({}, '', window.location.pathname + window.location.search)
    }
  }

  async function login(email, password) {
    const res = await authApi.login(email, password)
    // 2FA challenge — return the response so LoginView can show TOTP step
    if (res.data.requires_2fa) {
      return res.data  // { requires_2fa: true, temp_token }
    }
    token.value = res.data.access_token
    localStorage.setItem('token', token.value)
    await fetchMe()
    return res.data
  }

  async function verify2fa(tempToken, code) {
    const res = await authApi.verify2fa(tempToken, code)
    token.value = res.data.access_token
    localStorage.setItem('token', token.value)
    await fetchMe()
  }

  async function register(data) {
    const res = await authApi.register(data)
    return res.data   // return user so component can check email_verified
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

  return {
    user, token, isLoggedIn,
    login, verify2fa, register, fetchMe, logout, consumeOAuthToken,
  }
})
