<template>
  <div class="auth-screen">
    <div class="auth-left">
      <div class="grid-texture"></div>
      <div class="auth-logo animate-fade-down">
        <div class="logo-mark">A</div>
        <span class="logo-name">Axelo</span>
      </div>
      <div class="auth-hero animate-fade-up">
        <transition name="motto" mode="out-in">
          <h2 :key="currentMotto">
            {{ mottos[currentMotto].headline }}<br />
            <span>{{ mottos[currentMotto].highlight }}</span>
          </h2>
        </transition>
        <transition name="motto-sub" mode="out-in">
          <p :key="currentMotto">{{ mottos[currentMotto].sub }}</p>
        </transition>
        <div class="motto-dots">
          <span
            v-for="(_, i) in mottos"
            :key="i"
            class="motto-dot"
            :class="{ active: i === currentMotto }"
            @click="currentMotto = i"
          ></span>
        </div>
        <div class="feature-pills">
          <div class="pill" style="--delay:0.5s"><span class="dot" style="background:#10b981"></span> Kanban Boards</div>
          <div class="pill" style="--delay:0.65s"><span class="dot" style="background:#00d97e"></span> Sprint Planning</div>
          <div class="pill" style="--delay:0.8s"><span class="dot" style="background:#ff8c42"></span> Issue Tracking</div>
          <div class="pill" style="--delay:0.95s"><span class="dot" style="background:#ffd166"></span> Team Roles</div>
          <div class="pill" style="--delay:1.1s"><span class="dot" style="background:#06b6d4"></span> Self-Hostable</div>
        </div>
      </div>
      <div class="auth-footer animate-fade-up" style="--delay:0.3s">Open source · MIT License · Built with FastAPI + Vue 3</div>
    </div>

    <div class="auth-right">
      <!-- Step 1: credentials -->
      <div v-if="step === 'credentials'" class="auth-card" :class="{ shake: shaking }">
        <div class="card-eyebrow animate-field" style="--delay:0.1s">Welcome back</div>
        <h1 class="animate-field" style="--delay:0.2s">Sign in to Axelo</h1>
        <p class="subtitle animate-field" style="--delay:0.3s">Enter your credentials to continue</p>

        <transition name="error-pop">
          <div v-if="error" class="error-msg"><span class="error-icon">⚠</span> {{ error }}</div>
        </transition>

        <!-- Email not verified banner -->
        <transition name="error-pop">
          <div v-if="unverified" class="verify-banner">
            <div class="verify-banner-icon">📧</div>
            <div class="verify-banner-body">
              <div class="verify-banner-title">Email not verified</div>
              <div class="verify-banner-sub">Check your inbox for the verification link.</div>
            </div>
            <button class="verify-resend-btn" :disabled="resendSent" @click="resendVerification">
              {{ resendSent ? 'Sent ✓' : 'Resend' }}
            </button>
          </div>
        </transition>

        <div class="form-group animate-field" style="--delay:0.35s">
          <label class="fd-label" :class="{ 'label-active': emailFocused || email }">Email address</label>
          <div class="input-wrap" :class="{ focused: emailFocused, filled: email }">
            <span class="input-icon">✉</span>
            <input v-model="email" type="email" class="fd-input" placeholder="you@company.com"
              @focus="emailFocused=true" @blur="emailFocused=false" @keyup.enter="submit" />
          </div>
        </div>

        <div class="form-group animate-field" style="--delay:0.45s">
          <label class="fd-label" :class="{ 'label-active': passFocused || password }">Password</label>
          <div class="input-wrap" :class="{ focused: passFocused, filled: password }">
            <span class="input-icon">🔒</span>
            <input v-model="password" :type="showPass ? 'text' : 'password'" class="fd-input"
              placeholder="••••••••" @focus="passFocused=true" @blur="passFocused=false" @keyup.enter="submit" />
            <button class="toggle-pass" @click="showPass=!showPass" type="button" tabindex="-1">
              {{ showPass ? '🙈' : '👁' }}
            </button>
          </div>
        </div>

        <button class="btn-main animate-field" style="--delay:0.55s" @click="submit" :disabled="loading">
          <span v-if="!loading">Sign in</span>
          <span v-else class="btn-loader"><span></span><span class="dot-2"></span><span class="dot-3"></span></span>
        </button>

        <!-- SSO buttons -->
        <div class="sso-divider animate-field" style="--delay:0.6s"><span>or continue with</span></div>
        <div class="sso-row animate-field" style="--delay:0.65s">
          <a class="sso-btn" :href="oauthUrl('google')">
            <svg viewBox="0 0 24 24" width="18" height="18"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
            Google
          </a>
          <a class="sso-btn" :href="oauthUrl('github')">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>
            GitHub
          </a>
        </div>

        <div class="demo-hint animate-field" style="--delay:0.7s">
          <span class="hint-label">Demo</span>
          <button class="hint-btn" @click="fillDemo">Click to fill demo credentials</button>
        </div>

        <div class="auth-switch animate-field" style="--delay:0.75s">
          Don't have an account? <router-link to="/register">Sign up free</router-link>
        </div>
      </div>

      <!-- Step 2: 2FA TOTP challenge -->
      <div v-if="step === 'totp'" class="auth-card" :class="{ shake: shaking }">
        <div class="card-eyebrow">Two-Factor Auth</div>
        <h1>Enter your code</h1>
        <p class="subtitle">Open your authenticator app and enter the 6-digit code, or use a recovery code.</p>

        <transition name="error-pop">
          <div v-if="error" class="error-msg"><span class="error-icon">⚠</span> {{ error }}</div>
        </transition>

        <div class="form-group">
          <label class="fd-label" :class="{ 'label-active': codeFocused || totpCode }">6-digit code</label>
          <div class="input-wrap" :class="{ focused: codeFocused, filled: totpCode }">
            <span class="input-icon">🔐</span>
            <input v-model="totpCode" type="text" class="fd-input totp-input"
              placeholder="000000" maxlength="10" autocomplete="one-time-code"
              @focus="codeFocused=true" @blur="codeFocused=false" @keyup.enter="submitTotp" />
          </div>
        </div>

        <button class="btn-main" @click="submitTotp" :disabled="loading || !totpCode">
          <span v-if="!loading">Verify</span>
          <span v-else class="btn-loader"><span></span><span class="dot-2"></span><span class="dot-3"></span></span>
        </button>

        <div class="auth-switch" style="margin-top:1rem">
          <a href="#" @click.prevent="step='credentials'">← Back to login</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { authApi } from '@/api'

const mottos = [
  {
    headline: 'Ship projects',
    highlight: 'without the chaos.',
    sub: 'The open-source project tracker built for teams who want to move fast — without the Jira tax.',
  },
  {
    headline: 'Plan sprints,',
    highlight: 'ship with confidence.',
    sub: 'Powerful sprint planning and Kanban boards that keep your team aligned from kickoff to deploy.',
  },
  {
    headline: 'Track every issue,',
    highlight: 'miss nothing.',
    sub: 'Capture bugs, features, and tasks in one place — with real-time updates and full team visibility.',
  },
  {
    headline: 'Your team,',
    highlight: 'your rules.',
    sub: 'Flexible team roles and self-hostable infrastructure — total control over your workflow and data.',
  },
  {
    headline: 'Open source,',
    highlight: 'built to last.',
    sub: 'MIT licensed, FastAPI + Vue 3 powered. Extend it, fork it, own it — no vendor lock-in, ever.',
  },
]

const currentMotto = ref(0)
let mottoTimer = null

onMounted(() => {
  mottoTimer = setInterval(() => {
    currentMotto.value = (currentMotto.value + 1) % mottos.length
  }, 4000)
})

onUnmounted(() => {
  clearInterval(mottoTimer)
})

const router = useRouter()
const auth = useAuthStore()

const step = ref('credentials')
const email = ref('')
const password = ref('')
const totpCode = ref('')
const tempToken = ref('')
const loading = ref(false)
const error = ref('')
const unverified = ref(false)
const unverifiedEmail = ref('')
const resendSent = ref(false)
const shaking = ref(false)
const emailFocused = ref(false)
const passFocused = ref(false)
const codeFocused = ref(false)
const showPass = ref(false)

function oauthUrl(provider) {
  return `/api/auth/oauth/${provider}`
}

function fillDemo() {
  email.value = 'alex@axelo.dev'
  password.value = 'password123'
}

async function submit() {
  if (!email.value || !password.value) return
  loading.value = true; error.value = ''; unverified.value = false
  try {
    const result = await auth.login(email.value, password.value)
    if (result?.requires_2fa) {
      tempToken.value = result.temp_token
      step.value = 'totp'
    } else {
      router.push('/')
    }
  } catch (e) {
    const detail = e?.response?.data?.detail || ''
    if (detail === 'EMAIL_NOT_VERIFIED') {
      unverified.value = true
      unverifiedEmail.value = email.value
    } else {
      error.value = 'Invalid email or password. Please try again.'
      shaking.value = true
      setTimeout(() => { shaking.value = false }, 600)
    }
  } finally { loading.value = false }
}

async function submitTotp() {
  if (!totpCode.value) return
  loading.value = true; error.value = ''
  try {
    await auth.verify2fa(tempToken.value, totpCode.value)
    router.push('/')
  } catch {
    error.value = 'Invalid code. Please try again.'
    shaking.value = true
    setTimeout(() => { shaking.value = false }, 600)
  } finally { loading.value = false }
}

async function resendVerification() {
  try { await authApi.resendVerification(unverifiedEmail.value) } catch { /* enumeration-safe */ }
  resendSent.value = true
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
  background: linear-gradient(135deg, rgba(16,185,129,0.12) 0%, transparent 60%),
              radial-gradient(ellipse at 20% 80%, rgba(16,185,129,0.08) 0%, transparent 60%);
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
  box-shadow: 0 0 24px var(--accent-glow); animation: logoPulse 3s ease-in-out infinite;
}
@keyframes logoPulse {
  0%,100% { box-shadow: 0 0 16px var(--accent-glow); }
  50% { box-shadow: 0 0 32px var(--accent-glow), 0 0 8px rgba(16,185,129,0.4); }
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
  opacity: 0; animation: fadeUp 0.5s ease forwards; animation-delay: var(--delay, 0s);
}
.dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.auth-footer { font-size: 0.72rem; color: var(--text3); position: relative; z-index: 1; }
.auth-right { display: flex; align-items: center; justify-content: center; padding: 2rem; background: var(--bg); }
.auth-card {
  width: 100%; max-width: 420px;
  background: var(--bg2); border: 1px solid var(--border); border-radius: 20px;
  padding: 2.5rem; box-shadow: 0 24px 48px rgba(0,0,0,0.2);
}
.auth-card.shake { animation: shake 0.5s ease; }
@keyframes shake {
  0%,100% { transform: translateX(0); }
  20%,60% { transform: translateX(-6px); }
  40%,80% { transform: translateX(6px); }
}
.card-eyebrow { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent2); margin-bottom: 0.4rem; }
.auth-card h1 { font-family: var(--font-display); font-size: 1.9rem; font-weight: 800; letter-spacing: -0.035em; color: var(--text); margin-bottom: 0.35rem; line-height: 1.1; }
.subtitle { font-size: 0.88rem; color: var(--text2); margin-bottom: 2rem; }
.animate-field { opacity: 0; animation: fieldIn 0.45s ease forwards; animation-delay: var(--delay, 0s); }
@keyframes fieldIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.animate-fade-down { animation: fadeDown 0.6s ease both; }
@keyframes fadeDown { from { opacity: 0; transform: translateY(-16px); } to { opacity: 1; transform: translateY(0); } }
.animate-fade-up { opacity: 0; animation: fadeUp 0.6s ease forwards; animation-delay: var(--delay, 0.2s); }
@keyframes fadeUp { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
.error-msg { display: flex; align-items: center; gap: 8px; background: rgba(255,79,106,0.1); border: 1px solid rgba(255,79,106,0.3); border-radius: 8px; padding: 10px 14px; font-size: 0.82rem; color: var(--red); margin-bottom: 1.1rem; }
.error-icon { font-size: 0.9rem; }
.error-pop-enter-active { animation: errorIn 0.3s cubic-bezier(0.34,1.56,0.64,1); }
.error-pop-leave-active { animation: errorIn 0.2s reverse ease; }
@keyframes errorIn { from { opacity: 0; transform: scale(0.95) translateY(-6px); } to { opacity: 1; transform: scale(1) translateY(0); } }
.form-group { margin-bottom: 1.1rem; }
.fd-label { display: block; font-size: 0.78rem; font-weight: 600; color: var(--text2); margin-bottom: 6px; transition: color 0.2s; }
.fd-label.label-active { color: var(--accent2); }
.input-wrap { display: flex; align-items: center; gap: 8px; border: 1.5px solid var(--border2); border-radius: 10px; background: var(--bg2); padding: 0 12px; transition: border-color 0.2s, box-shadow 0.2s; }
.input-wrap.focused { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(16,185,129,0.18); }
.input-wrap.filled:not(.focused) { border-color: rgba(16,185,129,0.3); }
.input-icon { font-size: 0.85rem; opacity: 0.5; flex-shrink: 0; }
.fd-input { flex: 1; padding: 11px 0; border: none; outline: none; background: transparent; color: var(--text); font-size: 0.9rem; font-family: var(--font-body); }
.totp-input { font-family: var(--font-mono); font-size: 1.3rem; letter-spacing: 0.25em; }
.toggle-pass { background: none; border: none; cursor: pointer; padding: 0; font-size: 0.85rem; opacity: 0.5; transition: opacity 0.15s; }
.toggle-pass:hover { opacity: 1; }
.btn-main { width: 100%; padding: 13px; background: var(--accent); color: #fff; border: none; border-radius: 10px; font-family: var(--font-display); font-size: 0.9rem; font-weight: 700; cursor: pointer; margin-top: 0.25rem; box-shadow: 0 4px 20px rgba(16,185,129,0.3); transition: transform 0.15s, box-shadow 0.2s, opacity 0.15s; display: flex; align-items: center; justify-content: center; min-height: 46px; }
.btn-main:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(16,185,129,0.5); }
.btn-main:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-loader { display: flex; gap: 5px; align-items: center; }
.btn-loader span { width: 7px; height: 7px; border-radius: 50%; background: #fff; animation: bounce 0.8s ease-in-out infinite; }
.dot-2 { animation-delay: 0.15s !important; } .dot-3 { animation-delay: 0.3s !important; }
@keyframes bounce { 0%,60%,100% { transform: translateY(0); opacity: 0.6; } 30% { transform: translateY(-7px); opacity: 1; } }
.sso-divider { display: flex; align-items: center; gap: 10px; margin: 1.2rem 0 0.8rem; font-size: 0.75rem; color: var(--text3); }
.sso-divider::before,.sso-divider::after { content: ''; flex: 1; height: 1px; background: var(--border); }
.sso-row { display: flex; gap: 10px; margin-bottom: 1rem; }
.sso-btn { flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 10px; border: 1.5px solid var(--border2); border-radius: 10px; background: var(--bg); color: var(--text); font-size: 0.85rem; font-weight: 600; text-decoration: none; transition: border-color 0.2s, background 0.2s; cursor: pointer; }
.sso-btn:hover { border-color: var(--accent); background: rgba(16,185,129,0.06); }
.demo-hint { display: flex; align-items: center; gap: 8px; margin-top: 1rem; padding: 8px 12px; background: var(--bg2); border: 1px solid var(--border); border-radius: 8px; }
.hint-label { font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent2); background: rgba(16,185,129,0.1); padding: 2px 7px; border-radius: 4px; flex-shrink: 0; }
.hint-btn { background: none; border: none; color: var(--text3); font-size: 0.78rem; cursor: pointer; font-family: var(--font-mono); padding: 0; text-align: left; transition: color 0.15s; }
.hint-btn:hover { color: var(--text2); }
.auth-switch { text-align: center; margin-top: 1.25rem; font-size: 0.85rem; color: var(--text2); }
.auth-switch a { color: var(--accent2); font-weight: 500; text-decoration: none; }
.auth-switch a:hover { text-decoration: underline; }

.verify-banner {
  display: flex; align-items: center; gap: 12px;
  background: rgba(255,184,0,0.08); border: 1px solid rgba(255,184,0,0.25);
  border-radius: 8px; padding: 10px 14px; margin-bottom: 1.1rem;
}
.verify-banner-icon { font-size: 1.2rem; flex-shrink: 0; }
.verify-banner-body { flex: 1; min-width: 0; }
.verify-banner-title { font-size: 0.82rem; font-weight: 700; color: #ffb800; }
.verify-banner-sub { font-size: 0.76rem; color: var(--text3); margin-top: 1px; }
.verify-resend-btn {
  flex-shrink: 0; padding: 5px 12px; background: rgba(255,184,0,0.15);
  border: 1px solid rgba(255,184,0,0.3); border-radius: 6px;
  color: #ffb800; font-size: 0.78rem; font-weight: 700; cursor: pointer;
}
.verify-resend-btn:hover:not(:disabled) { background: rgba(255,184,0,0.25); }
.verify-resend-btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* Motto rotation transitions */
.motto-enter-active { transition: opacity 0.5s ease, transform 0.5s ease; }
.motto-leave-active { transition: opacity 0.35s ease, transform 0.35s ease; }
.motto-enter-from { opacity: 0; transform: translateY(14px); }
.motto-leave-to  { opacity: 0; transform: translateY(-10px); }

.motto-sub-enter-active { transition: opacity 0.5s ease 0.1s, transform 0.5s ease 0.1s; }
.motto-sub-leave-active { transition: opacity 0.3s ease; }
.motto-sub-enter-from { opacity: 0; transform: translateY(10px); }
.motto-sub-leave-to  { opacity: 0; }

/* Indicator dots */
.motto-dots { display: flex; gap: 6px; margin-top: 1.25rem; }
.motto-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: rgba(255,255,255,0.15); cursor: pointer;
  transition: background 0.3s, transform 0.3s;
}
.motto-dot.active { background: var(--accent2); transform: scale(1.4); }
.motto-dot:hover:not(.active) { background: rgba(255,255,255,0.35); }

</style>
