<template>
  <div class="verify-shell">
    <div class="verify-card">
      <div class="brand">🗂️ Axelo</div>

      <!-- Loading -->
      <div v-if="state === 'loading'" class="state-block">
        <div class="spinner"></div>
        <p class="state-msg">Verifying your email…</p>
      </div>

      <!-- Success -->
      <div v-else-if="state === 'success'" class="state-block">
        <div class="icon-wrap success-icon">✓</div>
        <h1 class="state-title">Email verified!</h1>
        <p class="state-msg">Your account is now active. You can sign in.</p>
        <router-link to="/login" class="btn-primary">Go to Login</router-link>
      </div>

      <!-- Expired -->
      <div v-else-if="state === 'expired'" class="state-block">
        <div class="icon-wrap warn-icon">⏱</div>
        <h1 class="state-title">Link expired</h1>
        <p class="state-msg">Verification links are valid for 24 hours. Request a new one below.</p>
        <div class="resend-form">
          <input
            v-model="resendEmail"
            type="email"
            placeholder="your@email.com"
            class="input"
            :disabled="resendSent"
          />
          <button class="btn-primary" :disabled="resendSent || !resendEmail" @click="resend">
            {{ resendSent ? 'Email sent ✓' : 'Resend verification email' }}
          </button>
        </div>
      </div>

      <!-- Error / invalid -->
      <div v-else class="state-block">
        <div class="icon-wrap error-icon">✕</div>
        <h1 class="state-title">Link not valid</h1>
        <p class="state-msg">{{ errorMsg }}</p>
        <div class="resend-form">
          <input
            v-model="resendEmail"
            type="email"
            placeholder="your@email.com"
            class="input"
            :disabled="resendSent"
          />
          <button class="btn-primary" :disabled="resendSent || !resendEmail" @click="resend">
            {{ resendSent ? 'Email sent ✓' : 'Resend verification email' }}
          </button>
        </div>
        <router-link to="/login" class="back-link">← Back to login</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { authApi } from '@/api'

const route  = useRoute()
const state  = ref('loading')   // loading | success | expired | error
const errorMsg   = ref('')
const resendEmail = ref('')
const resendSent  = ref(false)

onMounted(async () => {
  const token = route.query.token
  if (!token) {
    state.value = 'error'
    errorMsg.value = 'No verification token found in the URL.'
    return
  }
  try {
    await authApi.verifyEmail(token)
    state.value = 'success'
  } catch (err) {
    const detail = err?.response?.data?.detail || ''
    if (detail.toLowerCase().includes('expired')) {
      state.value = 'expired'
    } else {
      state.value = 'error'
      errorMsg.value = detail || 'This verification link is invalid or has already been used.'
    }
  }
})

async function resend() {
  if (!resendEmail.value) return
  try {
    await authApi.resendVerification(resendEmail.value)
  } catch {
    // Always show success — backend is enumeration-safe
  }
  resendSent.value = true
}
</script>

<style scoped>
.verify-shell {
  min-height: 100vh;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.verify-card {
  width: 100%;
  max-width: 420px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 2.5rem 2rem;
  text-align: center;
  box-shadow: 0 24px 80px rgba(0,0,0,0.4);
}

.brand {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--text3);
  margin-bottom: 2rem;
  letter-spacing: -0.3px;
}

.state-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.icon-wrap {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  font-weight: 800;
  margin-bottom: 0.25rem;
}

.success-icon { background: rgba(0,217,126,0.12); color: #00d97e; }
.warn-icon    { background: rgba(255,184,0,0.12);  color: #ffb800; }
.error-icon   { background: rgba(255,75,75,0.12);  color: #ff4b4b; }

.state-title {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--text);
  letter-spacing: -0.3px;
}

.state-msg {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text3);
  line-height: 1.5;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border);
  border-top-color: #10b981;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 0.5rem;
}
@keyframes spin { to { transform: rotate(360deg); } }

.btn-primary {
  display: inline-block;
  padding: 11px 28px;
  background: linear-gradient(135deg, #10b981, #06b6d4);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 700;
  font-size: 0.9rem;
  cursor: pointer;
  text-decoration: none;
  transition: opacity 0.15s;
  margin-top: 0.25rem;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary:not(:disabled):hover { opacity: 0.88; }

.resend-form {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  width: 100%;
  margin-top: 0.25rem;
}

.input {
  width: 100%;
  padding: 10px 14px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 0.9rem;
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s;
}
.input:focus { border-color: #10b981; }
.input:disabled { opacity: 0.5; }

.back-link {
  font-size: 0.82rem;
  color: var(--text3);
  text-decoration: none;
  margin-top: 0.5rem;
}
.back-link:hover { color: var(--text); }
</style>
