<template>
  <Teleport to="body">
    <Transition name="palette-fade">
      <div v-if="open" class="palette-overlay" @mousedown.self="close">
        <div class="palette-box">
          <div class="palette-input-row">
            <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            <input
              ref="inputRef"
              v-model="query"
              class="palette-input"
              placeholder="Search issues, projects…"
              @input="onInput"
              @keydown.down.prevent="move(1)"
              @keydown.up.prevent="move(-1)"
              @keydown.enter.prevent="confirm"
              @keydown.escape="close"
            />
            <span class="palette-esc" @click="close">Esc</span>
          </div>

          <div v-if="loading" class="palette-loading">
            <div class="palette-spinner"></div>
          </div>

          <div v-else-if="query.length >= 1" class="palette-results">
            <!-- Projects -->
            <div v-if="results.projects?.length" class="palette-group">
              <div class="palette-group-title">Projects</div>
              <div
                v-for="(p, i) in results.projects" :key="`p-${p.id}`"
                class="palette-item"
                :class="{ selected: cursor === i }"
                @mouseenter="cursor = i"
                @mousedown.prevent="goProject(p)"
              >
                <span class="item-icon project-icon">{{ p.key.slice(0,2) }}</span>
                <span class="item-main">{{ p.name }}</span>
                <span class="item-sub">{{ p.key }}</span>
              </div>
            </div>

            <!-- Issues -->
            <div v-if="results.issues?.length" class="palette-group">
              <div class="palette-group-title">Issues</div>
              <div
                v-for="(issue, i) in results.issues" :key="`i-${issue.id}`"
                class="palette-item"
                :class="{ selected: cursor === (results.projects?.length || 0) + i }"
                @mouseenter="cursor = (results.projects?.length || 0) + i"
                @mousedown.prevent="goIssue(issue)"
              >
                <span class="item-dot" :class="`type-${issue.type}`"></span>
                <span class="item-key">{{ issue.key }}</span>
                <span class="item-main">{{ issue.title }}</span>
                <span class="status-badge" :class="`status-${issue.status}`">{{ issue.status.replace('_',' ') }}</span>
              </div>
            </div>

            <div v-if="!results.projects?.length && !results.issues?.length" class="palette-empty">
              No results for "{{ query }}"
            </div>
          </div>

          <div v-else class="palette-hint">
            <div class="hint-row"><kbd>↑↓</kbd> navigate &nbsp; <kbd>↵</kbd> select &nbsp; <kbd>Esc</kbd> close</div>
            <div class="hint-row recent" v-if="recent.length">
              <span class="recent-label">Recent:</span>
              <span v-for="r in recent" :key="r.id" class="recent-chip" @mousedown.prevent="goIssue(r)">{{ r.key }}</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { searchApi } from '@/api'

const open    = ref(false)
const query   = ref('')
const results = ref({ issues: [], projects: [] })
const loading = ref(false)
const cursor  = ref(0)
const inputRef = ref(null)
const recent  = ref(JSON.parse(localStorage.getItem('axelo-recent') || '[]').slice(0, 5))
const router  = useRouter()
let debounceTimer = null

// Keyboard shortcut: Cmd+K / Ctrl+K
function onKeydown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    toggle()
  }
}

function toggle() {
  open.value = !open.value
  if (open.value) {
    query.value = ''
    results.value = { issues: [], projects: [] }
    cursor.value = 0
    nextTick(() => inputRef.value?.focus())
  }
}

function close() { open.value = false }

function onInput() {
  clearTimeout(debounceTimer)
  if (query.value.length < 1) { results.value = { issues: [], projects: [] }; return }
  loading.value = true
  debounceTimer = setTimeout(async () => {
    try {
      const res = await searchApi.query(query.value)
      results.value = res.data
      cursor.value = 0
    } finally { loading.value = false }
  }, 200)
}

const allItems = () => [
  ...(results.value.projects || []).map(p => ({ ...p, _type: 'project' })),
  ...(results.value.issues   || []).map(i => ({ ...i, _type: 'issue'   })),
]

function move(dir) {
  const total = allItems().length
  if (!total) return
  cursor.value = (cursor.value + dir + total) % total
}

function confirm() {
  const items = allItems()
  if (!items.length) return
  const item = items[cursor.value]
  if (item._type === 'project') goProject(item)
  else goIssue(item)
}

function goProject(p) {
  router.push(`/projects/${p.id}`)
  close()
}
function goIssue(issue) {
  const r = { id: issue.id, key: issue.key, project_id: issue.project_id }
  recent.value = [r, ...recent.value.filter(x => x.id !== r.id)].slice(0, 5)
  localStorage.setItem('axelo-recent', JSON.stringify(recent.value))
  router.push(`/projects/${issue.project_id}/issues/${issue.id}`)
  close()
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))

// Expose open() for navbar button
defineExpose({ toggle })
</script>

<style scoped>
.palette-overlay {
  position: fixed; inset: 0; z-index: 9000;
  background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);
  display: flex; align-items: flex-start; justify-content: center;
  padding-top: 12vh;
}
.palette-fade-enter-active { animation: palIn 0.18s cubic-bezier(0.22,1,0.36,1); }
.palette-fade-leave-active { animation: palIn 0.1s ease reverse; }
@keyframes palIn {
  from { opacity:0; transform: scale(0.97) translateY(-8px); }
  to   { opacity:1; transform: scale(1) translateY(0); }
}

.palette-box {
  width: 560px; max-width: calc(100vw - 2rem);
  background: var(--bg2); border: 1px solid var(--border2);
  border-radius: 14px; box-shadow: 0 32px 80px rgba(0,0,0,0.6);
  overflow: hidden;
}

.palette-input-row {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px; border-bottom: 1px solid var(--border);
}
.search-icon { color: var(--text3); flex-shrink: 0; }
.palette-input {
  flex: 1; background: none; border: none; outline: none;
  font-size: 1rem; color: var(--text); font-family: var(--font-body);
}
.palette-input::placeholder { color: var(--text3); }
.palette-esc {
  font-size: 0.68rem; color: var(--text3); background: var(--bg3);
  border: 1px solid var(--border2); padding: 2px 6px; border-radius: 4px;
  cursor: pointer; flex-shrink: 0;
}

.palette-results { max-height: 420px; overflow-y: auto; padding: 8px 0; }
.palette-group { padding: 0 8px 4px; }
.palette-group-title {
  font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--text3); padding: 6px 8px 4px;
}
.palette-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 8px; cursor: pointer; transition: background 0.1s;
}
.palette-item.selected, .palette-item:hover { background: rgba(16,185,129,0.12); }
.item-icon.project-icon {
  width: 24px; height: 24px; border-radius: 5px;
  background: rgba(16,185,129,0.15); color: var(--accent2);
  font-size: 0.62rem; font-weight: 700; font-family: var(--font-mono);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.item-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.type-bug   { background: var(--red); }
.type-story { background: var(--green); }
.type-task  { background: var(--accent2); }
.type-epic  { background: #06b6d4; }
.item-key { font-family: var(--font-mono); font-size: 0.7rem; color: var(--text3); flex-shrink: 0; }
.item-main { flex: 1; font-size: 0.85rem; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-sub  { font-size: 0.72rem; color: var(--text3); }
.status-badge {
  font-size: 0.65rem; font-weight: 600; padding: 1px 7px; border-radius: 8px; text-transform: capitalize; flex-shrink: 0;
}
.status-todo        { background: rgba(144,144,176,0.15); color: var(--text2); }
.status-in_progress { background: rgba(16,185,129,0.15); color: var(--accent2); }
.status-in_review   { background: rgba(255,209,102,0.15); color: #ffd166; }
.status-done        { background: rgba(0,217,126,0.15); color: var(--green); }

.palette-empty { padding: 2rem 1rem; text-align: center; font-size: 0.85rem; color: var(--text2); }
.palette-loading { display: flex; justify-content: center; padding: 2rem; }
.palette-spinner {
  width: 24px; height: 24px; border-radius: 50%;
  border: 2px solid var(--border2); border-top-color: var(--accent);
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.palette-hint { padding: 1rem 1.5rem; }
.hint-row {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.75rem; color: var(--text3); margin-bottom: 0.5rem;
}
kbd {
  background: var(--bg3); border: 1px solid var(--border2);
  border-radius: 4px; padding: 1px 5px; font-size: 0.7rem; color: var(--text2);
}
.recent { flex-wrap: wrap; }
.recent-label { color: var(--text3); font-size: 0.72rem; }
.recent-chip {
  background: rgba(16,185,129,0.1); color: var(--accent2);
  font-family: var(--font-mono); font-size: 0.68rem;
  padding: 2px 8px; border-radius: 4px; cursor: pointer;
  transition: background 0.1s;
}
.recent-chip:hover { background: rgba(16,185,129,0.2); }
</style>
