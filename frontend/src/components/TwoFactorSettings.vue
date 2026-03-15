<template>
  <div class="tfa-panel">
    <div class="tfa-header">
      <div>
        <h3 class="panel-title">Two-Factor Authentication</h3>
        <p class="panel-sub">Add an extra layer of security with a TOTP authenticator app.</p>
      </div>
      <div class="tfa-badge" :class="enabled ? 'badge-on' : 'badge-off'">
        {{ enabled ? '✓ Enabled' : 'Disabled' }}
      </div>
    </div>

    <!-- Not enabled: show setup flow -->
    <div v-if="!enabled">
      <div v-if="!setupData">
        <p class="tfa-desc">
          Use apps like <strong>Google Authenticator</strong>, <strong>Authy</strong>, or <strong>1Password</strong>
          to generate time-based codes.
        </p>
        <button class="btn-primary" @click="startSetup" :disabled="loading">
          {{ loading ? 'Loading…' : 'Set up 2FA' }}
        </button>
      </div>

      <!-- QR code + verification step -->
      <div v-else class="setup-flow">
        <div class="step-block">
          <div class="step-num">1</div>
          <div>
            <div class="step-title">Scan QR code</div>
            <p class="step-desc">Open your authenticator app and scan this code.</p>
            <div class="qr-box">
              <canvas ref="qrCanvas" class="qr-canvas"></canvas>
            </div>
            <details class="manual-entry">
              <summary>Can't scan? Enter manually</summary>
              <code class="secret-text">{{ setupData.secret }}</code>
            </details>
          </div>
        </div>

        <div class="step-block">
          <div class="step-num">2</div>
          <div class="step-full">
            <div class="step-title">Enter verification code</div>
            <p class="step-desc">Enter the 6-digit code from your app to confirm setup.</p>
            <transition name="err">
              <div v-if="error" class="err-msg">{{ error }}</div>
            </transition>
            <div class="code-row">
              <input v-model="verifyCode" type="text" class="code-input" placeholder="000000"
                maxlength="6" autocomplete="one-time-code" @keyup.enter="confirmSetup" />
              <button class="btn-primary" @click="confirmSetup" :disabled="loading || !verifyCode">
                {{ loading ? '…' : 'Enable 2FA' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Enabled: show recovery codes or disable flow -->
    <div v-else>
      <div v-if="recoveryCodes.length" class="recovery-box">
        <div class="recovery-header">
          <span class="warn-icon">⚠</span>
          <strong>Save your recovery codes</strong>
        </div>
        <p class="recovery-desc">These 10 single-use codes let you access your account if you lose your authenticator. Save them somewhere safe — they won't be shown again.</p>
        <div class="codes-grid">
          <code v-for="c in recoveryCodes" :key="c" class="recovery-code">{{ c }}</code>
        </div>
        <button class="btn-outline" @click="copyCodes">📋 Copy all codes</button>
      </div>

      <div v-else>
        <div class="tfa-active-note">
          🔐 Your account is protected by 2FA. You'll be asked for a code on every login.
        </div>

        <div v-if="!disabling">
          <button class="btn-danger-outline" @click="disabling = true">Disable 2FA</button>
        </div>

        <div v-else class="disable-flow">
          <p class="step-desc">Enter your current TOTP code to disable 2FA.</p>
          <transition name="err">
            <div v-if="error" class="err-msg">{{ error }}</div>
          </transition>
          <div class="code-row">
            <input v-model="disableCode" type="text" class="code-input" placeholder="000000"
              maxlength="6" @keyup.enter="confirmDisable" />
            <button class="btn-danger" @click="confirmDisable" :disabled="loading || !disableCode">
              {{ loading ? '…' : 'Disable' }}
            </button>
            <button class="btn-ghost" @click="disabling=false">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { authApi } from '@/api'

const enabled = ref(false)
const loading = ref(false)
const error = ref('')
const setupData = ref(null)
const verifyCode = ref('')
const recoveryCodes = ref([])
const disabling = ref(false)
const disableCode = ref('')
const qrCanvas = ref(null)

onMounted(async () => {
  const res = await authApi.tfa_status()
  enabled.value = res.data.enabled
})

async function startSetup() {
  loading.value = true; error.value = ''
  try {
    const res = await authApi.tfa_setup()
    setupData.value = res.data
    await nextTick()
    await renderQR(res.data.uri)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to start setup'
  } finally { loading.value = false }
}

async function renderQR(uri) {
  // Use a simple QR library via dynamic import or fallback to text URI
  try {
    const QRCode = (await import('qrcode')).default
    QRCode.toCanvas(qrCanvas.value, uri, { width: 200, margin: 2, color: { dark: '#10b981', light: '#0d1a12' } })
  } catch {
    // qrcode not available client-side — show the URI as text
    if (qrCanvas.value) {
      qrCanvas.value.style.display = 'none'
    }
  }
}

async function confirmSetup() {
  if (!verifyCode.value) return
  loading.value = true; error.value = ''
  try {
    const res = await authApi.tfa_enable(setupData.value.secret, verifyCode.value)
    enabled.value = true
    recoveryCodes.value = res.data.recovery_codes
    setupData.value = null
  } catch (e) {
    error.value = e.response?.data?.detail || 'Invalid code'
  } finally { loading.value = false }
}

async function confirmDisable() {
  if (!disableCode.value) return
  loading.value = true; error.value = ''
  try {
    await authApi.tfa_disable(disableCode.value)
    enabled.value = false
    disabling.value = false
    disableCode.value = ''
  } catch (e) {
    error.value = e.response?.data?.detail || 'Invalid code'
  } finally { loading.value = false }
}

function copyCodes() {
  navigator.clipboard.writeText(recoveryCodes.value.join('\n'))
}
</script>

<style scoped>
.tfa-panel { background: var(--bg2); border: 1px solid var(--border); border-radius: 14px; padding: 1.5rem; }
.tfa-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.25rem; gap: 1rem; }
.panel-title { font-size: 1rem; font-weight: 700; color: var(--text); margin-bottom: 0.2rem; }
.panel-sub { font-size: 0.82rem; color: var(--text2); }
.tfa-badge { padding: 4px 12px; border-radius: 100px; font-size: 0.75rem; font-weight: 700; flex-shrink: 0; }
.badge-on { background: rgba(0,217,126,0.12); color: var(--green); border: 1px solid rgba(0,217,126,0.3); }
.badge-off { background: var(--bg3); color: var(--text3); border: 1px solid var(--border); }
.tfa-desc { font-size: 0.85rem; color: var(--text2); margin-bottom: 1rem; line-height: 1.6; }
.setup-flow { display: flex; flex-direction: column; gap: 1.5rem; margin-top: 1rem; }
.step-block { display: flex; gap: 1rem; }
.step-num { width: 28px; height: 28px; border-radius: 50%; background: var(--accent); color: #fff; font-size: 0.8rem; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px; }
.step-full { flex: 1; }
.step-title { font-size: 0.9rem; font-weight: 700; color: var(--text); margin-bottom: 0.3rem; }
.step-desc { font-size: 0.82rem; color: var(--text2); margin-bottom: 0.75rem; line-height: 1.5; }
.qr-box { background: #0d1a12; border-radius: 10px; padding: 12px; display: inline-block; margin-bottom: 0.75rem; }
.qr-canvas { display: block; border-radius: 6px; }
.manual-entry { margin-top: 0.5rem; }
.manual-entry summary { font-size: 0.78rem; color: var(--accent2); cursor: pointer; }
.secret-text { display: block; font-family: var(--font-mono); font-size: 0.78rem; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 6px 10px; margin-top: 0.5rem; color: var(--text2); word-break: break-all; }
.code-row { display: flex; gap: 8px; align-items: center; }
.code-input { flex: 1; max-width: 140px; padding: 9px 12px; border: 1.5px solid var(--border2); border-radius: 8px; background: var(--bg); color: var(--text); font-family: var(--font-mono); font-size: 1.1rem; letter-spacing: 0.2em; outline: none; }
.code-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(16,185,129,0.15); }
.err-msg { background: rgba(255,79,106,0.1); border: 1px solid rgba(255,79,106,0.3); border-radius: 8px; padding: 8px 12px; font-size: 0.82rem; color: var(--red); margin-bottom: 0.75rem; }
.err-enter-active { animation: errIn 0.2s ease; }
@keyframes errIn { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
.recovery-box { background: rgba(255,209,30,0.06); border: 1px solid rgba(255,209,30,0.25); border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; }
.recovery-header { display: flex; align-items: center; gap: 8px; font-size: 0.9rem; color: var(--yellow); margin-bottom: 0.5rem; }
.warn-icon { font-size: 1rem; }
.recovery-desc { font-size: 0.82rem; color: var(--text2); line-height: 1.5; margin-bottom: 1rem; }
.codes-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; margin-bottom: 1rem; }
.recovery-code { font-family: var(--font-mono); font-size: 0.82rem; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 5px 8px; color: var(--text); text-align: center; }
.tfa-active-note { background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2); border-radius: 10px; padding: 10px 14px; font-size: 0.85rem; color: var(--text2); margin-bottom: 1rem; }
.disable-flow { margin-top: 1rem; }
.btn-primary { padding: 9px 18px; background: var(--accent); color: #fff; border: none; border-radius: 8px; font-size: 0.85rem; font-weight: 700; cursor: pointer; transition: opacity 0.15s; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-outline { padding: 7px 14px; background: transparent; border: 1px solid var(--border2); border-radius: 8px; color: var(--text2); font-size: 0.82rem; cursor: pointer; transition: border-color 0.2s; }
.btn-outline:hover { border-color: var(--accent); color: var(--accent); }
.btn-danger { padding: 9px 18px; background: var(--red); color: #fff; border: none; border-radius: 8px; font-size: 0.85rem; font-weight: 700; cursor: pointer; }
.btn-danger:disabled { opacity: 0.5; }
.btn-danger-outline { padding: 7px 14px; background: transparent; border: 1px solid rgba(255,79,106,0.4); border-radius: 8px; color: var(--red); font-size: 0.82rem; cursor: pointer; transition: background 0.2s; }
.btn-danger-outline:hover { background: rgba(255,79,106,0.08); }
.btn-ghost { padding: 9px 14px; background: transparent; border: none; color: var(--text3); font-size: 0.85rem; cursor: pointer; }
</style>
