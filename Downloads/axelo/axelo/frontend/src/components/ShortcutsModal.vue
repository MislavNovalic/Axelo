<template>
  <Teleport to="body">
    <div v-if="open" class="shortcuts-backdrop" @click.self="$emit('close')">
      <div class="shortcuts-modal">
        <div class="shortcuts-header">
          <span class="shortcuts-title">Keyboard Shortcuts</span>
          <button class="close-btn" @click="$emit('close')">✕</button>
        </div>
        <div class="shortcuts-body">
          <div class="group" v-for="group in groups" :key="group.label">
            <div class="group-label">{{ group.label }}</div>
            <div class="shortcut-row" v-for="s in group.shortcuts" :key="s.keys.join('')">
              <div class="keys">
                <kbd v-for="k in s.keys" :key="k">{{ k }}</kbd>
              </div>
              <div class="desc">{{ s.desc }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({ open: Boolean })
defineEmits(['close'])

const groups = [
  {
    label: 'Global',
    shortcuts: [
      { keys: ['Ctrl', 'K'], desc: 'Open global search' },
      { keys: ['?'], desc: 'Show this shortcuts panel' },
      { keys: ['Esc'], desc: 'Close any open modal or panel' },
    ],
  },
  {
    label: 'Issues',
    shortcuts: [
      { keys: ['C'], desc: 'Create new issue (when not typing)' },
    ],
  },
]
</script>

<style scoped>
.shortcuts-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.55);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; backdrop-filter: blur(2px);
}
.shortcuts-modal {
  width: 440px; max-width: 92vw;
  background: var(--bg2); border: 1px solid var(--border2);
  border-radius: 14px; box-shadow: 0 24px 60px rgba(0,0,0,0.45);
  overflow: hidden;
}
.shortcuts-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; border-bottom: 1px solid var(--border);
}
.shortcuts-title { font-size: 0.88rem; font-weight: 600; color: var(--text); }
.close-btn {
  background: none; border: none; color: var(--text3);
  cursor: pointer; font-size: 1rem; padding: 0;
}
.close-btn:hover { color: var(--text); }

.shortcuts-body { padding: 12px 18px 18px; }
.group { margin-bottom: 16px; }
.group:last-child { margin-bottom: 0; }
.group-label {
  font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.09em;
  color: var(--text3); font-weight: 600; margin-bottom: 8px;
}
.shortcut-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 5px 0; border-bottom: 1px solid var(--border);
}
.shortcut-row:last-child { border-bottom: none; }
.keys { display: flex; gap: 4px; }
kbd {
  font-family: var(--font-mono); font-size: 0.72rem;
  background: var(--bg3); border: 1px solid var(--border2);
  border-radius: 5px; padding: 2px 7px; color: var(--text2);
}
.desc { font-size: 0.78rem; color: var(--text2); }
</style>
