import { onMounted, onUnmounted } from 'vue'

const INPUT_TAGS = new Set(['INPUT', 'TEXTAREA', 'SELECT'])

/**
 * Register global keyboard shortcuts.
 *
 * Usage:
 *   useKeyboardShortcuts({
 *     'ctrl+k': () => openSearch(),
 *     'c':      () => createIssue(),
 *     '?':      () => showHelp(),
 *   })
 *
 * Single-letter shortcuts are suppressed when focus is in an input field.
 */
export function useKeyboardShortcuts(shortcuts = {}) {
  function handler(e) {
    const tag = document.activeElement?.tagName
    const isEditing = INPUT_TAGS.has(tag) || document.activeElement?.isContentEditable

    const parts = []
    if (e.ctrlKey || e.metaKey) parts.push('ctrl')
    if (e.shiftKey) parts.push('shift')
    if (e.altKey) parts.push('alt')
    parts.push(e.key.toLowerCase())
    const combo = parts.join('+')

    const action = shortcuts[combo]
    if (!action) return

    const isSingleChar = combo.length === 1
    if (isSingleChar && isEditing) return

    e.preventDefault()
    action(e)
  }

  onMounted(() => window.addEventListener('keydown', handler))
  onUnmounted(() => window.removeEventListener('keydown', handler))
}
