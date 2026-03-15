<template>
  <div class="time-panel">
    <div class="time-header">
      <h4 class="panel-title">⏱ Time Tracking</h4>
      <span class="total-badge">{{ formatMinutes(total) }} total</span>
    </div>

    <!-- Log time form -->
    <div class="log-form" v-if="canWrite">
      <div class="log-row">
        <input v-model="inputMinutes" type="number" min="1" max="14400"
          class="time-input" placeholder="mins" @keyup.enter="submit" />
        <input v-model="inputDesc" type="text" class="desc-input" placeholder="What did you work on?" maxlength="200" @keyup.enter="submit" />
        <button class="btn-log" @click="submit" :disabled="!inputMinutes || submitting">
          {{ submitting ? '…' : 'Log' }}
        </button>
      </div>
      <div class="quick-btns">
        <button v-for="q in quickOptions" :key="q.mins" class="quick-btn" @click="quickLog(q.mins)">
          {{ q.label }}
        </button>
      </div>
    </div>

    <!-- Log list -->
    <div v-if="logs.length" class="log-list">
      <div v-for="log in logs" :key="log.id" class="log-entry">
        <div class="log-left">
          <span class="log-user">{{ log.user_name }}</span>
          <span class="log-time">{{ formatMinutes(log.minutes) }}</span>
          <span v-if="log.description" class="log-desc">{{ log.description }}</span>
        </div>
        <div class="log-right">
          <span class="log-date">{{ fmtDate(log.logged_at) }}</span>
          <button v-if="canDelete(log)" class="btn-del" @click="remove(log.id)" title="Delete">✕</button>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">No time logged yet.</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { timeApi } from '@/api'
import { useAuthStore } from '@/store/auth'

const props = defineProps({
  projectId: { type: Number, required: true },
  issueId: { type: Number, required: true },
  canWrite: { type: Boolean, default: true },
  isAdmin: { type: Boolean, default: false },
})

const auth = useAuthStore()
const logs = ref([])
const total = ref(0)
const inputMinutes = ref('')
const inputDesc = ref('')
const submitting = ref(false)

const quickOptions = [
  { label: '15m', mins: 15 },
  { label: '30m', mins: 30 },
  { label: '1h', mins: 60 },
  { label: '2h', mins: 120 },
  { label: '4h', mins: 240 },
]

function formatMinutes(m) {
  if (!m) return '0m'
  const h = Math.floor(m / 60)
  const min = m % 60
  if (h && min) return `${h}h ${min}m`
  if (h) return `${h}h`
  return `${min}m`
}

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function canDelete(log) {
  return props.isAdmin || log.user_id === auth.user?.id
}

async function fetchLogs() {
  const res = await timeApi.list(props.projectId, props.issueId)
  logs.value = res.data.logs
  total.value = res.data.total_minutes
}

async function submit() {
  if (!inputMinutes.value || submitting.value) return
  submitting.value = true
  try {
    await timeApi.log(props.projectId, props.issueId, {
      minutes: parseInt(inputMinutes.value),
      description: inputDesc.value || null,
    })
    inputMinutes.value = ''
    inputDesc.value = ''
    await fetchLogs()
  } finally { submitting.value = false }
}

async function quickLog(mins) {
  submitting.value = true
  try {
    await timeApi.log(props.projectId, props.issueId, { minutes: mins })
    await fetchLogs()
  } finally { submitting.value = false }
}

async function remove(logId) {
  await timeApi.delete(props.projectId, props.issueId, logId)
  await fetchLogs()
}

onMounted(fetchLogs)
</script>

<style scoped>
.time-panel { margin-top: 1.5rem; }
.time-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; }
.panel-title { font-size: 0.85rem; font-weight: 700; color: var(--text2); margin: 0; }
.total-badge { font-size: 0.75rem; font-weight: 700; background: rgba(16,185,129,0.12); color: var(--accent2); padding: 2px 8px; border-radius: 100px; }
.log-form { margin-bottom: 1rem; }
.log-row { display: flex; gap: 6px; margin-bottom: 6px; }
.time-input { width: 70px; padding: 7px 10px; border: 1.5px solid var(--border2); border-radius: 8px; background: var(--bg); color: var(--text); font-size: 0.85rem; outline: none; }
.time-input:focus { border-color: var(--accent); }
.desc-input { flex: 1; padding: 7px 10px; border: 1.5px solid var(--border2); border-radius: 8px; background: var(--bg); color: var(--text); font-size: 0.85rem; outline: none; }
.desc-input:focus { border-color: var(--accent); }
.btn-log { padding: 7px 14px; background: var(--accent); color: #fff; border: none; border-radius: 8px; font-size: 0.82rem; font-weight: 700; cursor: pointer; white-space: nowrap; }
.btn-log:disabled { opacity: 0.5; cursor: not-allowed; }
.quick-btns { display: flex; gap: 5px; flex-wrap: wrap; }
.quick-btn { padding: 4px 10px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg2); color: var(--text3); font-size: 0.75rem; cursor: pointer; transition: border-color 0.15s, color 0.15s; }
.quick-btn:hover { border-color: var(--accent); color: var(--accent2); }
.log-list { display: flex; flex-direction: column; gap: 4px; max-height: 240px; overflow-y: auto; }
.log-entry { display: flex; align-items: center; justify-content: space-between; padding: 7px 10px; border-radius: 8px; background: var(--bg2); border: 1px solid var(--border); font-size: 0.8rem; }
.log-left { display: flex; align-items: center; gap: 8px; min-width: 0; }
.log-user { font-weight: 600; color: var(--text); white-space: nowrap; }
.log-time { font-family: var(--font-mono); color: var(--accent2); font-weight: 700; white-space: nowrap; }
.log-desc { color: var(--text3); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.log-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.log-date { color: var(--text3); white-space: nowrap; }
.btn-del { background: none; border: none; color: var(--text3); cursor: pointer; font-size: 0.7rem; padding: 2px 4px; border-radius: 4px; transition: color 0.15s; }
.btn-del:hover { color: var(--red); }
.empty-state { font-size: 0.82rem; color: var(--text3); text-align: center; padding: 1rem 0; }
</style>
