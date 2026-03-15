/**
 * Global keyboard shortcuts — P1
 * C           → create issue (if on a project page)
 * G then B    → go to board
 * G then L    → go to backlog
 * G then T    → go to team
 * G then R    → go to reports
 * G then M    → go to roadmap
 * G then A    → go to AI sprint planner
 * G then I    → go to importer
 * ?           → toggle shortcuts help overlay
 */
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'

export const shortcutsVisible = ref(false)

export function useKeyboardShortcuts({ onCreateIssue } = {}) {
  const router = useRouter()
  const route  = useRoute()
  let gPressed = false
  let gTimer   = null

  function getProjectId() {
    return route.params.id ? Number(route.params.id) : null
  }

  function isTyping() {
    const tag = document.activeElement?.tagName
    return tag === 'INPUT' || tag === 'TEXTAREA' || document.activeElement?.isContentEditable
  }

  function handleKey(e) {
    if (isTyping()) return
    const key = e.key

    if (gPressed) {
      clearTimeout(gTimer)
      gPressed = false
      const pid = getProjectId()
      if (pid) {
        if (key === 'b') router.push(`/projects/${pid}`)
        if (key === 'l') router.push(`/projects/${pid}/backlog`)
        if (key === 't') router.push(`/projects/${pid}/team`)
        if (key === 'r') router.push(`/projects/${pid}/reports`)
        if (key === 'm') router.push(`/projects/${pid}/roadmap`)
        if (key === 'a') router.push(`/projects/${pid}/ai/sprint-planner`)
        if (key === 'i') router.push(`/projects/${pid}/import`)
      }
      return
    }

    if (key === 'g') {
      gPressed = true
      gTimer = setTimeout(() => { gPressed = false }, 800)
    } else if (key === 'c') {
      if (getProjectId() && onCreateIssue) onCreateIssue()
    } else if (key === '?') {
      shortcutsVisible.value = !shortcutsVisible.value
    }
  }

  onMounted(() => document.addEventListener('keydown', handleKey))
  onBeforeUnmount(() => document.removeEventListener('keydown', handleKey))

  return { shortcutsVisible }
}
