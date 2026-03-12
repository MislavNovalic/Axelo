<template>
  <slot v-if="!hasError" />
  <div v-else class="error-boundary">
    <div class="error-card">
      <div class="error-icon">⚠️</div>
      <h2 class="error-title">Something went wrong</h2>
      <p class="error-msg">{{ errorMessage }}</p>
      <div class="error-actions">
        <button class="btn-primary" @click="reset">Try again</button>
        <button class="btn-ghost" @click="goHome">Go to dashboard</button>
      </div>
      <details v-if="isDev" class="error-details">
        <summary>Error details</summary>
        <pre>{{ errorStack }}</pre>
      </details>
    </div>
  </div>
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const hasError    = ref(false)
const errorMessage = ref('')
const errorStack  = ref('')
const isDev       = import.meta.env.DEV

onErrorCaptured((err) => {
  hasError.value     = true
  errorMessage.value = err?.message || 'An unexpected error occurred'
  errorStack.value   = err?.stack   || ''
  console.error('[ErrorBoundary]', err)
  return false // prevent propagation
})

function reset() {
  hasError.value = false
  errorMessage.value = ''
  errorStack.value   = ''
}

function goHome() {
  reset()
  router.push('/')
}
</script>

<style scoped>
.error-boundary {
  min-height: 60vh; display: flex; align-items: center;
  justify-content: center; padding: 2rem;
}
.error-card {
  background: var(--bg2); border: 1px solid rgba(255,79,106,0.25);
  border-radius: 16px; padding: 2.5rem 2rem;
  max-width: 480px; width: 100%; text-align: center;
}
.error-icon { font-size: 2.5rem; margin-bottom: 1rem; }
.error-title {
  font-family: var(--font-display); font-size: 1.25rem;
  font-weight: 700; color: var(--text); margin-bottom: 0.5rem;
}
.error-msg { font-size: 0.875rem; color: var(--text2); margin-bottom: 1.5rem; }
.error-actions { display: flex; gap: 0.75rem; justify-content: center; }
.btn-primary {
  background: var(--accent); color: #fff; border: none;
  padding: 8px 20px; border-radius: 8px; cursor: pointer;
  font-size: 0.85rem; font-family: var(--font-body);
  transition: opacity 0.15s;
}
.btn-primary:hover { opacity: 0.85; }
.btn-ghost {
  background: none; border: 1px solid var(--border2); color: var(--text2);
  padding: 8px 20px; border-radius: 8px; cursor: pointer;
  font-size: 0.85rem; font-family: var(--font-body);
}
.btn-ghost:hover { color: var(--text); }
.error-details {
  margin-top: 1.5rem; text-align: left; font-size: 0.7rem; color: var(--text3);
}
.error-details pre {
  background: var(--bg3); padding: 0.75rem; border-radius: 6px;
  overflow: auto; max-height: 200px; font-family: var(--font-mono);
}
</style>
