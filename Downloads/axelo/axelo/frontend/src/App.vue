<template>
  <div v-if="crashed" class="error-boundary">
    <div class="error-box">
      <div class="error-icon">⚠️</div>
      <div class="error-title">Something went wrong</div>
      <div class="error-msg">{{ errorMessage }}</div>
      <button class="btn-primary" @click="recover">Reload page</button>
    </div>
  </div>
  <template v-else>
    <router-view />
    <SearchPalette :open="searchOpen" @close="searchOpen = false" />
    <ShortcutsModal :open="shortcutsOpen" @close="shortcutsOpen = false" />
  </template>
</template>

<script setup>
import { ref, onErrorCaptured, provide } from 'vue'
import { useRouter } from 'vue-router'
import SearchPalette from '@/components/SearchPalette.vue'
import ShortcutsModal from '@/components/ShortcutsModal.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'

const router = useRouter()
const searchOpen = ref(false)
const shortcutsOpen = ref(false)
const crashed = ref(false)
const errorMessage = ref('')

// Provide search/shortcuts controls to child components via injection
provide('openSearch', () => { searchOpen.value = true })
provide('openShortcuts', () => { shortcutsOpen.value = true })
provide('openCreateIssue', () => {
  // Emitted down via the current view — handled in Navbar
  document.dispatchEvent(new CustomEvent('axelo:create-issue'))
})

// Global keyboard shortcuts
useKeyboardShortcuts({
  'ctrl+k': () => { searchOpen.value = true },
  '?': () => { shortcutsOpen.value = true },
  'escape': () => {
    searchOpen.value = false
    shortcutsOpen.value = false
  },
  'c': () => {
    document.dispatchEvent(new CustomEvent('axelo:create-issue'))
  },
})

// Frontend error boundary (A05 / resilience fix)
onErrorCaptured((err, instance, info) => {
  console.error('[Axelo] Uncaught error:', err, info)
  errorMessage.value = err?.message || 'An unexpected error occurred.'
  crashed.value = true
  return false
})

function recover() {
  crashed.value = false
  errorMessage.value = ''
  window.location.reload()
}
</script>

<style>
.error-boundary {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: var(--bg);
}
.error-box {
  text-align: center; padding: 2rem; max-width: 400px;
  background: var(--bg2); border: 1px solid var(--border2);
  border-radius: 14px;
}
.error-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
.error-title { font-size: 1.1rem; font-weight: 600; color: var(--text); margin-bottom: 0.5rem; }
.error-msg { font-size: 0.82rem; color: var(--text2); margin-bottom: 1.25rem; }
</style>
