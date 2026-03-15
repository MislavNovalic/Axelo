<template>
  <Teleport to="body">
    <Transition name="shortcuts-fade">
      <div v-if="shortcutsVisible" class="shortcuts-overlay" @click.self="shortcutsVisible = false">
        <div class="shortcuts-panel">
          <div class="panel-header">
            <h2>Keyboard Shortcuts</h2>
            <button class="close-btn" @click="shortcutsVisible = false">✕</button>
          </div>
          <div class="shortcuts-grid">
            <div v-for="group in groups" :key="group.title" class="shortcut-group">
              <div class="group-title">{{ group.title }}</div>
              <div v-for="s in group.shortcuts" :key="s.keys.join('')" class="shortcut-row">
                <div class="keys">
                  <kbd v-for="k in s.keys" :key="k">{{ k }}</kbd>
                </div>
                <span class="shortcut-desc">{{ s.desc }}</span>
              </div>
            </div>
          </div>
          <p class="shortcut-hint">Press <kbd>?</kbd> again to close</p>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { shortcutsVisible } from '@/composables/useKeyboardShortcuts'

const groups = [
  {
    title: 'Global',
    shortcuts: [
      { keys: ['⌘', 'K'], desc: 'Open search palette' },
      { keys: ['C'],       desc: 'Create issue (on a project page)' },
      { keys: ['?'],       desc: 'Show/hide shortcuts' },
    ],
  },
  {
    title: 'Navigation (press G then…)',
    shortcuts: [
      { keys: ['G', 'B'], desc: 'Go to Board' },
      { keys: ['G', 'L'], desc: 'Go to Backlog' },
      { keys: ['G', 'T'], desc: 'Go to Team' },
      { keys: ['G', 'R'], desc: 'Go to Reports' },
      { keys: ['G', 'M'], desc: 'Go to Roadmap' },
      { keys: ['G', 'A'], desc: 'Go to AI Sprint Planner' },
      { keys: ['G', 'I'], desc: 'Go to Importer' },
    ],
  },
  {
    title: 'Issue View',
    shortcuts: [
      { keys: ['E'],       desc: 'Edit title (when focused)' },
      { keys: ['Esc'],     desc: 'Close modal / cancel edit' },
    ],
  },
]
</script>

<style scoped>
.shortcuts-overlay {
  position: fixed; inset: 0; z-index: 9100;
  background: rgba(0,0,0,0.55); backdrop-filter: blur(3px);
  display: flex; align-items: center; justify-content: center;
}
.shortcuts-fade-enter-active { animation: fadeIn 0.18s ease; }
.shortcuts-fade-leave-active { animation: fadeIn 0.1s ease reverse; }
@keyframes fadeIn { from { opacity:0; transform: scale(0.97); } to { opacity:1; transform: scale(1); } }

.shortcuts-panel {
  background: var(--bg2); border: 1px solid var(--border2);
  border-radius: 14px; box-shadow: 0 24px 64px rgba(0,0,0,0.5);
  padding: 1.5rem; width: 480px; max-width: calc(100vw - 2rem);
  max-height: 80vh; overflow-y: auto;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 1.25rem;
}
.panel-header h2 {
  font-family: var(--font-display); font-size: 1rem;
  font-weight: 700; color: var(--text);
}
.close-btn {
  background: none; border: none; cursor: pointer;
  color: var(--text3); font-size: 0.9rem; padding: 2px 6px;
}
.close-btn:hover { color: var(--text); }

.shortcuts-grid { display: flex; flex-direction: column; gap: 1.25rem; }
.shortcut-group {}
.group-title {
  font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--text3); margin-bottom: 0.5rem;
}
.shortcut-row {
  display: flex; align-items: center; gap: 10px;
  padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.03);
}
.keys { display: flex; gap: 3px; min-width: 100px; }
kbd {
  background: var(--bg3); border: 1px solid var(--border2);
  border-radius: 4px; padding: 2px 7px; font-size: 0.72rem;
  font-family: var(--font-mono); color: var(--text2);
}
.shortcut-desc { font-size: 0.82rem; color: var(--text2); }
.shortcut-hint {
  margin-top: 1rem; text-align: center;
  font-size: 0.72rem; color: var(--text3);
}
.shortcut-hint kbd { font-size: 0.65rem; }
</style>
