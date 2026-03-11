<template>
  <div class="auth-screen">
    <div class="auth-left">
      <div class="grid-texture"></div>
      <div class="auth-logo">
        <div class="logo-mark">A</div>
        <span class="logo-name">Axelo</span>
      </div>
      <div class="auth-hero">
        <h2>Ship projects<br /><span>without the chaos.</span></h2>
        <p>The open-source project tracker built for teams who want to move fast — without the Jira tax.</p>
        <div class="feature-pills">
          <div class="pill"><span class="dot" style="background:#5c4fff"></span> Kanban Boards</div>
          <div class="pill"><span class="dot" style="background:#00d97e"></span> Sprint Planning</div>
          <div class="pill"><span class="dot" style="background:#ff8c42"></span> Issue Tracking</div>
          <div class="pill"><span class="dot" style="background:#ffd166"></span> Team Roles</div>
          <div class="pill"><span class="dot" style="background:#bb5cf7"></span> Self-Hostable</div>
        </div>
      </div>
      <div class="auth-footer">Open source · MIT License · Built with FastAPI + Vue 3</div>
    </div>

    <div class="auth-right">
      <div class="auth-card">
        <h1>Welcome back</h1>
        <p class="subtitle">Sign in to your Axelo workspace</p>
        <div v-if="error" class="error-msg">{{ error }}</div>
        <div class="form-group">
          <label class="fd-label">Email address</label>
          <input v-model="email" type="email" class="fd-input" placeholder="you@company.com" @keyup.enter="submit" />
        </div>
        <div class="form-group">
          <label class="fd-label">Password</label>
          <input v-model="password" type="password" class="fd-input" placeholder="••••••••" @keyup.enter="submit" />
        </div>
        <button class="btn-main" :disabled="loading" @click="submit">
          {{ loading ? 'Signing in...' : 'Sign in →' }}
        </button>
        <p class="auth-switch">
          Don't have an account? <router-link to="/register">Create one</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const auth = useAuthStore()
const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  if (!email.value || !password.value) return
  loading.value = true; error.value = ''
  try {
    await auth.login(email.value, password.value)
    router.push('/')
  } catch {
    error.value = 'Invalid email or password. Please try again.'
  } finally { loading.value = false }
}
</script>

<style scoped>
.auth-screen { min-height: 100vh; display: grid; grid-template-columns: 1fr 1fr; }
.auth-left {
  background: var(--bg2); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; justify-content: space-between;
  padding: 2.5rem; position: relative; overflow: hidden;
}
.auth-left::before {
  content: ''; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(135deg, rgba(92,79,255,0.12) 0%, transparent 60%),
              radial-gradient(ellipse at 20% 80%, rgba(92,79,255,0.08) 0%, transparent 60%);
}
.grid-texture {
  position: absolute; inset: 0; pointer-events: none;
  background-image: linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: 40px 40px;
}
.auth-logo { display: flex; align-items: center; gap: 10px; position: relative; z-index: 1; }
.logo-mark {
  width: 36px; height: 36px; background: var(--accent); border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-weight: 800; font-size: 18px; color: #fff;
  box-shadow: 0 0 24px var(--accent-glow);
}
.logo-name { font-family: var(--font-display); font-size: 1.2rem; font-weight: 700; letter-spacing: -0.02em; color: var(--text); }
.auth-hero { position: relative; z-index: 1; }
.auth-hero h2 {
  font-family: var(--font-display); font-size: 2.6rem; font-weight: 800;
  line-height: 1.1; letter-spacing: -0.04em; color: var(--text); margin-bottom: 1rem;
}
.auth-hero h2 span { color: var(--accent2); }
.auth-hero p { font-size: 0.95rem; color: var(--text2); line-height: 1.6; max-width: 320px; }
.feature-pills { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 1.5rem; }
.pill {
  display: flex; align-items: center; gap: 6px; padding: 6px 12px;
  border-radius: 100px; background: rgba(255,255,255,0.05); border: 1px solid var(--border);
  font-size: 0.78rem; color: var(--text2);
}
.pill .dot { width: 6px; height: 6px; border-radius: 50%; }
.auth-footer { font-size: 0.78rem; color: var(--text3); position: relative; z-index: 1; }
.auth-right { display: flex; align-items: center; justify-content: center; padding: 2rem; background: var(--bg); }
.auth-card { width: 100%; max-width: 380px; }
.auth-card h1 {
  font-family: var(--font-display); font-size: 1.7rem; font-weight: 700;
  letter-spacing: -0.03em; color: var(--text); margin-bottom: 0.4rem;
}
.subtitle { font-size: 0.88rem; color: var(--text2); margin-bottom: 2rem; }
.form-group { margin-bottom: 1rem; }
.error-msg {
  background: rgba(255,79,106,0.1); border: 1px solid rgba(255,79,106,0.3);
  border-radius: 6px; padding: 9px 12px; font-size: 0.82rem; color: var(--red); margin-bottom: 1rem;
}
.btn-main {
  width: 100%; padding: 11px; background: var(--accent); color: #fff; border: none;
  border-radius: 8px; font-family: var(--font-display); font-size: 0.9rem; font-weight: 600;
  cursor: pointer; transition: background 0.2s, transform 0.1s, box-shadow 0.2s;
  margin-top: 0.5rem; box-shadow: 0 4px 20px rgba(92,79,255,0.3);
}
.btn-main:hover { background: var(--accent2); box-shadow: 0 4px 28px rgba(92,79,255,0.5); transform: translateY(-1px); }
.btn-main:active { transform: translateY(0); }
.btn-main:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.auth-switch { text-align: center; margin-top: 1.5rem; font-size: 0.85rem; color: var(--text2); }
.auth-switch a { color: var(--accent2); font-weight: 500; text-decoration: none; }
.auth-switch a:hover { text-decoration: underline; }
</style>
