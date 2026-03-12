<template>
  <Teleport to="body">
    <div v-if="open" class="palette-backdrop" @click.self="close">
      <div class="palette">
        <div class="palette-input-wrap">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <input
            ref="inputRef"
            v-model="query"
            class="palette-input"
            placeholder="Search issues, projects, comments…"
            @keydown.escape="close"
            @keydown.arrow-down.prevent="moveDown"
            @keydown.arrow-up.prevent="moveUp"
            @keydown.enter.prevent="selectCurrent"
          />
          <kbd class="esc-hint">esc</kbd>
        </div>

        <div class="palette-body">
          <div v-if="loading" class="palette-status">Searching…</div>
          <div v-else-if="query.length > 0 && isEmpty" class="palette-status">No results for "{{ query }}"</div>
          <div v-else-if="!query" class="palette-status">
            <div class="recent-label">Recent searches</div>
            <div
              v-for="r in recentSearches"
              :key="r"
              class="recent-item"
              @click="query = r"
            >🕐 {{ r }}</div>
            <div v-if="!recentSearches.length" class="palette-hint">Type to search across all projects</div>
          </div>

          <template v-else>
            <section v-if="results.issues?.length">
              <div class="section-label">Issues</div>
              <div
                v-for="(item, i) in results.issues"
                :key="`issue-${item.id}`"
                class="palette-item"
                :class="{ active: activeIdx === flatIdx(0, i) }"
                @click="goIssue(item)"
                @mouseenter="activeIdx = flatIdx(0, i)"
              >
                <span class="item-icon">{{ issueTypeIcon(item.type) }}</span>
                <span class="item-key">{{ item.key }}</span>
                <span class="item-title">{{ item.title }}</span>
                <span class="item-meta" :style="`color:${statusColor(item.status)}`">{{ item.status }}</span>
              </div>
            </section>

            <section v-if="results.projects?.length">
              <div class="section-label">Projects</div>
              <div
                v-for="(item, i) in results.projects"
                :key="`proj-${item.id}`"
                class="palette-item"
                :class="{ active: activeIdx === flatIdx(1, i) }"
                @click="goProject(item)"
                @mouseenter="activeIdx = flatIdx(1, i)"
              >
                <span class="item-icon">📁</span>
                <span class="item-key">{{ item.key }}</span>
                <span class="item-title">{{ item.name }}</span>
              </div>
            </section>

            <section v-if="results.comments?.length">
              <div class="section-label">Comments</div>
              <div
                v-for="(item, i) in results.comments"
                :key="`comment-${item.id}`"
                class="palette-item"
                :class="{ active: activeIdx === flatIdx(2, i) }"
                @click="goComment(item)"
                @mouseenter="activeIdx = flatIdx(2, i)"
              >
                <span class="item-icon">💬</span>
                <span class="item-key">{{ item.issue_key }}</span>
                <span class="item-title">{{ item.body }}</span>
              </div>
            </section>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { searchApi } from '@/api'

const props = defineProps({ open: Boolean })
const emit = defineEmits(['close'])
const router = useRouter()

const query = ref('')
const results = ref({ issues: [], projects: [], comments: [] })
const loading = ref(false)
const activeIdx = ref(0)
const inputRef = ref(null)

const recentSearches = ref(
  JSON.parse(localStorage.getItem('axelo-recent-searches') || '[]')
)

const isEmpty = computed(() =>
  !results.value.issues?.length && !results.value.projects?.length && !results.value.comments?.length
)

const allItems = computed(() => [
  ...(results.value.issues || []).map(i => ({ type: 'issue', ...i })),
  ...(results.value.projects || []).map(p => ({ type: 'project', ...p })),
  ...(results.value.comments || []).map(c => ({ type: 'comment', ...c })),
])

function flatIdx(section, i) {
  const offsets = [0, results.value.issues?.length || 0, (results.value.issues?.length || 0) + (results.value.projects?.length || 0)]
  return offsets[section] + i
}

let debounce = null
watch(query, (val) => {
  clearTimeout(debounce)
  if (!val || val.length < 1) { results.value = { issues: [], projects: [], comments: [] }; return }
  loading.value = true
  debounce = setTimeout(async () => {
    try {
      const res = await searchApi.search(val)
      results.value = res.data
      activeIdx.value = 0
    } finally {
      loading.value = false
    }
  }, 200)
})

watch(() => props.open, (val) => {
  if (val) {
    query.value = ''
    results.value = { issues: [], projects: [], comments: [] }
    nextTick(() => inputRef.value?.focus())
  }
})

function close() { emit('close') }

function saveRecent(q) {
  if (!q) return
  const list = [q, ...recentSearches.value.filter(r => r !== q)].slice(0, 5)
  recentSearches.value = list
  localStorage.setItem('axelo-recent-searches', JSON.stringify(list))
}

function moveDown() {
  activeIdx.value = Math.min(activeIdx.value + 1, allItems.value.length - 1)
}
function moveUp() {
  activeIdx.value = Math.max(activeIdx.value - 1, 0)
}
function selectCurrent() {
  const item = allItems.value[activeIdx.value]
  if (!item) return
  if (item.type === 'issue') goIssue(item)
  else if (item.type === 'project') goProject(item)
  else if (item.type === 'comment') goComment(item)
}

function goIssue(item) {
  saveRecent(query.value)
  router.push(`/projects/${item.project_id}/issues/${item.id}`)
  close()
}
function goProject(item) {
  saveRecent(query.value)
  router.push(`/projects/${item.id}`)
  close()
}
function goComment(item) {
  saveRecent(query.value)
  router.push(`/projects/${item.project_id}/issues/${item.issue_id}`)
  close()
}

function issueTypeIcon(type) {
  const icons = { bug: '🐛', story: '📗', task: '✅', epic: '⚡' }
  return icons[type] || '📌'
}

function statusColor(status) {
  const map = { done: 'var(--green)', in_progress: 'var(--accent)', in_review: 'var(--yellow)' }
  return map[status] || 'var(--text3)'
}
</script>

<style scoped>
.palette-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  display: flex; align-items: flex-start; justify-content: center;
  padding-top: 15vh; z-index: 1000; backdrop-filter: blur(2px);
}

.palette {
  width: 600px; max-width: 92vw;
  background: var(--bg2); border: 1px solid var(--border2);
  border-radius: 14px; box-shadow: 0 32px 80px rgba(0,0,0,0.5);
  overflow: hidden;
}

.palette-input-wrap {
  display: flex; align-items: center; gap: 10px;
  padding: 14px 16px; border-bottom: 1px solid var(--border);
}
.search-icon { color: var(--text3); flex-shrink: 0; }
.palette-input {
  flex: 1; background: none; border: none; outline: none;
  font-size: 0.95rem; color: var(--text);
}
.palette-input::placeholder { color: var(--text3); }
.esc-hint {
  font-size: 0.65rem; color: var(--text3);
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: 4px; padding: 2px 5px; font-family: var(--font-mono);
}

.palette-body { max-height: 420px; overflow-y: auto; padding: 6px 0; }

.palette-status { padding: 16px 18px; font-size: 0.82rem; color: var(--text3); }
.palette-hint { font-size: 0.78rem; color: var(--text3); margin-top: 4px; }
.recent-label { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.07em; color: var(--text3); margin-bottom: 4px; }
.recent-item {
  padding: 6px 0; font-size: 0.8rem; color: var(--text2);
  cursor: pointer; border-radius: 4px;
}
.recent-item:hover { color: var(--text); }

.section-label {
  font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.09em;
  color: var(--text3); padding: 8px 16px 4px; font-weight: 600;
}

.palette-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px; cursor: pointer; transition: background 0.1s;
}
.palette-item:hover, .palette-item.active { background: rgba(92,79,255,0.1); }
.item-icon { font-size: 0.9rem; flex-shrink: 0; }
.item-key { font-family: var(--font-mono); font-size: 0.72rem; color: var(--accent2); flex-shrink: 0; }
.item-title { flex: 1; font-size: 0.82rem; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-meta { font-size: 0.7rem; flex-shrink: 0; }
</style>
