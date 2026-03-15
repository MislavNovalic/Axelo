<template>
  <div class="app-shell">
    <Navbar />
    <div class="shell-body">

      <!-- Sidebar -->
      <aside class="sidebar">
        <router-link to="/" class="sidebar-item"><span class="icon">⬛</span> Overview</router-link>
        <div class="sidebar-item active"><span class="icon">📅</span> My Calendar</div>
        <div class="sidebar-section-title">Legend</div>
        <div class="legend-item"><span class="leg-dot" style="background:#10b981"></span> Task</div>
        <div class="legend-item"><span class="leg-dot" style="background:#ff4f6a"></span> Bug</div>
        <div class="legend-item"><span class="leg-dot" style="background:#00d97e"></span> Story</div>
        <div class="legend-item"><span class="leg-dot" style="background:#06b6d4"></span> Epic</div>
        <div class="sidebar-section-title" style="margin-top:1rem;">Status filter</div>
        <label v-for="s in statuses" :key="s.value" class="filter-check">
          <input type="checkbox" :value="s.value" v-model="activeStatuses" />
          <span class="check-dot" :style="`background:${s.color}`"></span>
          {{ s.label }}
        </label>
      </aside>

      <!-- Calendar -->
      <main class="cal-main">
        <!-- Header -->
        <div class="cal-header">
          <div class="cal-nav">
            <button class="nav-btn" @click="prevMonth">‹</button>
            <h1 class="cal-title">{{ monthName }} {{ year }}</h1>
            <button class="nav-btn" @click="nextMonth">›</button>
            <button class="today-btn" @click="goToday">Today</button>
          </div>
          <div class="cal-meta">
            <span class="meta-pill">{{ filteredIssues.length }} issue{{ filteredIssues.length !== 1 ? 's' : '' }} this month</span>
            <span class="meta-pill overdue" v-if="overdueCount > 0">{{ overdueCount }} overdue</span>
          </div>
        </div>

        <!-- Day labels -->
        <div class="day-labels">
          <div v-for="d in dayLabels" :key="d" class="day-label">{{ d }}</div>
        </div>

        <!-- Grid -->
        <div class="cal-grid" v-if="!loading">
          <div
            v-for="cell in calendarCells"
            :key="cell.key"
            class="cal-cell"
            :class="{
              'other-month': !cell.currentMonth,
              'is-today': cell.isToday,
              'is-weekend': cell.isWeekend,
            }"
            @click="openDayModal(cell)"
          >
            <div class="cell-number" :class="{ 'today-badge': cell.isToday }">
              {{ cell.day }}
            </div>
            <div class="cell-issues">
              <div
                v-for="issue in cell.issues.slice(0, 3)"
                :key="issue.id"
                class="cell-issue-chip"
                :class="`type-${issue.type}`"
                :style="priorityBorder(issue.priority)"
                @click.stop="openIssueModal(issue)"
                :title="issue.title"
              >
                <span class="chip-key">{{ issue.key }}</span>
                <span class="chip-title">{{ issue.title }}</span>
                <span class="chip-status" :class="`status-${issue.status}`"></span>
              </div>
              <div v-if="cell.issues.length > 3" class="cell-more" @click.stop="openDayModal(cell)">
                +{{ cell.issues.length - 3 }} more
              </div>
            </div>
          </div>
        </div>

        <div v-else class="cal-loading">
          <div class="spinner"></div> Loading your calendar...
        </div>
      </main>
    </div>

    <!-- Day modal -->
    <div v-if="dayModal" class="modal-overlay" @click.self="dayModal = null">
      <div class="modal">
        <div class="modal-head">
          <div>
            <div class="modal-date-label">{{ formatModalDate(dayModal.date) }}</div>
            <h2>{{ dayModal.issues.length }} issue{{ dayModal.issues.length !== 1 ? 's' : '' }} due</h2>
          </div>
          <button class="modal-close" @click="dayModal = null">✕</button>
        </div>
        <div class="modal-issue-list">
          <div
            v-for="issue in dayModal.issues" :key="issue.id"
            class="modal-issue-row"
            :class="`type-${issue.type}`"
            @click="openIssueModal(issue); dayModal = null"
          >
            <div class="row-type-dot" :class="`dot-${issue.type}`"></div>
            <div class="row-content">
              <div class="row-key-title">
                <span class="row-key">{{ issue.key }}</span>
                <span class="row-title">{{ issue.title }}</span>
              </div>
              <div class="row-badges">
                <span class="badge-pill" :class="`priority-${issue.priority}`">{{ issue.priority }}</span>
                <span class="badge-pill" :class="`status-pill-${issue.status}`">{{ issue.status.replace('_',' ') }}</span>
              </div>
            </div>
          </div>
          <div v-if="!dayModal.issues.length" class="modal-empty">No issues due on this day.</div>
        </div>
      </div>
    </div>

    <!-- Issue detail modal -->
    <div v-if="issueModal" class="modal-overlay" @click.self="issueModal = null">
      <div class="modal issue-modal">
        <div class="modal-head">
          <div>
            <div class="modal-date-label">{{ issueModal.project_key }} · Due {{ formatShort(issueModal.due_date) }}</div>
            <h2>{{ issueModal.title }}</h2>
          </div>
          <button class="modal-close" @click="issueModal = null">✕</button>
        </div>
        <div class="issue-modal-body">
          <div class="issue-modal-row">
            <span class="im-label">Key</span>
            <span class="im-val mono">{{ issueModal.key }}</span>
          </div>
          <div class="issue-modal-row">
            <span class="im-label">Type</span>
            <span class="im-val"><span class="type-badge-sm" :class="`type-${issueModal.type}`">{{ issueModal.type }}</span></span>
          </div>
          <div class="issue-modal-row">
            <span class="im-label">Priority</span>
            <span class="im-val"><span class="badge-pill" :class="`priority-${issueModal.priority}`">{{ issueModal.priority }}</span></span>
          </div>
          <div class="issue-modal-row">
            <span class="im-label">Status</span>
            <span class="im-val"><span class="badge-pill" :class="`status-pill-${issueModal.status}`">{{ issueModal.status.replace('_',' ') }}</span></span>
          </div>
          <div class="issue-modal-row">
            <span class="im-label">Due date</span>
            <input type="date" class="fd-input" style="max-width:180px;" :value="issueModal.due_date" @change="updateDueDate(issueModal, $event.target.value)" />
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-ghost" @click="issueModal = null">Close</button>
          <router-link :to="`/projects/${issueModal.project_id}/issues/${issueModal.id}`" class="btn-primary" style="text-decoration:none;" @click="issueModal = null">
            Open Issue →
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import Navbar from '@/components/Navbar.vue'
import { calendarApi } from '@/api'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const today = new Date()
const year  = ref(today.getFullYear())
const month = ref(today.getMonth() + 1) // 1-based
const issues = ref([])
const loading = ref(false)
const dayModal = ref(null)
const issueModal = ref(null)

const activeStatuses = ref(['backlog','todo','in_progress','in_review','done'])
const statuses = [
  { value: 'todo',        label: 'To Do',       color: '#90b09a' },
  { value: 'in_progress', label: 'In Progress',  color: '#10b981' },
  { value: 'in_review',   label: 'In Review',    color: '#ffd166' },
  { value: 'done',        label: 'Done',         color: '#00d97e' },
  { value: 'backlog',     label: 'Backlog',      color: '#4a6455' },
]

const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December']
const dayLabels = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat']

const monthName = computed(() => MONTHS[month.value - 1])
const filteredIssues = computed(() => issues.value.filter(i => activeStatuses.value.includes(i.status)))
const overdueCount = computed(() => {
  const t = today.toISOString().slice(0,10)
  return filteredIssues.value.filter(i => i.due_date < t && i.status !== 'done').length
})

const calendarCells = computed(() => {
  const firstDay = new Date(year.value, month.value - 1, 1).getDay()
  const daysInMonth = new Date(year.value, month.value, 0).getDate()
  const daysInPrev  = new Date(year.value, month.value - 1, 0).getDate()
  const todayStr = today.toISOString().slice(0,10)
  const cells = []

  // Previous month padding
  for (let i = firstDay - 1; i >= 0; i--) {
    const d = daysInPrev - i
    const dateStr = `${year.value}-${String(month.value - 1 || 12).padStart(2,'0')}-${String(d).padStart(2,'0')}`
    cells.push({ key: `prev-${d}`, day: d, currentMonth: false, isToday: false, isWeekend: false, issues: [], date: dateStr })
  }

  // Current month
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year.value}-${String(month.value).padStart(2,'0')}-${String(d).padStart(2,'0')}`
    const dow = new Date(year.value, month.value - 1, d).getDay()
    const dayIssues = filteredIssues.value.filter(i => i.due_date === dateStr)
    cells.push({
      key: dateStr, day: d, currentMonth: true,
      isToday: dateStr === todayStr,
      isWeekend: dow === 0 || dow === 6,
      issues: dayIssues, date: dateStr,
    })
  }

  // Next month padding to fill 6 rows
  const remaining = 42 - cells.length
  for (let d = 1; d <= remaining; d++) {
    const dateStr = `${year.value}-${String(month.value + 1 > 12 ? 1 : month.value + 1).padStart(2,'0')}-${String(d).padStart(2,'0')}`
    cells.push({ key: `next-${d}`, day: d, currentMonth: false, isToday: false, isWeekend: false, issues: [], date: dateStr })
  }

  return cells
})

async function fetchIssues() {
  loading.value = true
  try {
    const res = await calendarApi.getMonth(year.value, month.value)
    issues.value = res.data
  } finally {
    loading.value = false }
}

function prevMonth() {
  if (month.value === 1) { month.value = 12; year.value-- } else month.value--
}
function nextMonth() {
  if (month.value === 12) { month.value = 1; year.value++ } else month.value++
}
function goToday() { year.value = today.getFullYear(); month.value = today.getMonth() + 1 }

function openDayModal(cell) {
  if (!cell.currentMonth || !cell.issues.length) return
  dayModal.value = cell
}
function openIssueModal(issue) { issueModal.value = issue }

async function updateDueDate(issue, newDate) {
  await calendarApi.setDueDate(issue.id, newDate)
  issue.due_date = newDate
  await fetchIssues()
}

function formatModalDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('en-US', { weekday:'long', month:'long', day:'numeric', year:'numeric' })
}
function formatShort(dateStr) {
  if (!dateStr) return '—'
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' })
}
function priorityBorder(priority) {
  const map = { critical: '#ff4f6a', high: '#ff8c42', medium: '#ffd166', low: '#10b981' }
  return `border-left: 2px solid ${map[priority] || '#333'}`
}

watch([year, month], fetchIssues)
onMounted(fetchIssues)
</script>

<style scoped>
.app-shell { display:flex; flex-direction:column; min-height:100vh; background:var(--bg); }
.shell-body { display:flex; flex:1; height:calc(100vh - 52px); overflow:hidden; }

/* Sidebar */
.sidebar {
  width:200px; flex-shrink:0; background:var(--bg2); border-right:1px solid var(--border);
  display:flex; flex-direction:column; padding:1rem 0.75rem; gap:2px; overflow-y:auto;
}
.sidebar-section-title {
  font-size:0.68rem; font-weight:600; text-transform:uppercase; letter-spacing:0.08em;
  color:var(--text3); padding:0.5rem 0.5rem 0.25rem;
}
.sidebar-item {
  display:flex; align-items:center; gap:8px; padding:7px 10px; border-radius:7px;
  font-size:0.84rem; color:var(--text2); cursor:pointer; transition:all 0.15s; text-decoration:none;
}
.sidebar-item:hover { background:rgba(255,255,255,0.05); color:var(--text); }
.sidebar-item.active { background:rgba(16,185,129,0.15); color:var(--accent2); }
.icon { font-size:0.9rem; width:18px; text-align:center; }
.legend-item {
  display:flex; align-items:center; gap:8px; padding:5px 10px;
  font-size:0.8rem; color:var(--text2);
}
.leg-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.filter-check {
  display:flex; align-items:center; gap:8px; padding:5px 10px;
  font-size:0.8rem; color:var(--text2); cursor:pointer;
}
.filter-check input { display:none; }
.check-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; opacity:0.4; transition:opacity 0.15s; }
.filter-check:has(input:checked) .check-dot { opacity:1; }
.filter-check:has(input:checked) { color:var(--text); }

/* Calendar main */
.cal-main { flex:1; overflow:auto; padding:1.5rem 1.75rem; display:flex; flex-direction:column; gap:1rem; }

.cal-header { display:flex; align-items:center; justify-content:space-between; }
.cal-nav { display:flex; align-items:center; gap:10px; }
.cal-title {
  font-family:var(--font-display); font-size:1.4rem; font-weight:700;
  letter-spacing:-0.03em; color:var(--text); min-width:220px; text-align:center;
}
.nav-btn {
  width:32px; height:32px; border-radius:8px; border:1px solid var(--border);
  background:var(--bg2); color:var(--text2); cursor:pointer; font-size:1.1rem;
  display:flex; align-items:center; justify-content:center; transition:all 0.15s;
}
.nav-btn:hover { border-color:var(--border2); color:var(--text); }
.today-btn {
  padding:5px 14px; border-radius:7px; border:1px solid var(--border);
  background:var(--bg2); color:var(--text2); cursor:pointer; font-size:0.8rem;
  font-family:var(--font-body); transition:all 0.15s;
}
.today-btn:hover { border-color:var(--accent); color:var(--accent2); }
.cal-meta { display:flex; align-items:center; gap:8px; }
.meta-pill {
  font-size:0.75rem; padding:4px 10px; border-radius:100px;
  background:rgba(255,255,255,0.05); border:1px solid var(--border); color:var(--text2);
}
.meta-pill.overdue { background:rgba(255,79,106,0.1); border-color:rgba(255,79,106,0.2); color:var(--red); }

/* Day labels */
.day-labels { display:grid; grid-template-columns:repeat(7,1fr); gap:2px; margin-bottom:2px; }
.day-label { text-align:center; font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:0.06em; color:var(--text3); padding:6px 0; }

/* Grid */
.cal-grid { display:grid; grid-template-columns:repeat(7,1fr); grid-template-rows:repeat(6,1fr); gap:2px; flex:1; min-height:0; }
.cal-cell {
  background:var(--bg2); border:1px solid var(--border); border-radius:8px;
  padding:6px; cursor:pointer; transition:border-color 0.15s;
  display:flex; flex-direction:column; min-height:90px; overflow:hidden;
}
.cal-cell:hover { border-color:var(--border2); }
.cal-cell.other-month { background:var(--bg); opacity:0.4; pointer-events:none; }
.cal-cell.is-today { border-color:rgba(16,185,129,0.5); background:rgba(16,185,129,0.05); }
.cal-cell.is-weekend { background:rgba(255,255,255,0.015); }

.cell-number {
  font-size:0.78rem; font-weight:600; color:var(--text3);
  width:22px; height:22px; display:flex; align-items:center; justify-content:center;
  border-radius:50%; margin-bottom:4px; flex-shrink:0;
}
.cell-number.today-badge { background:var(--accent); color:#fff; }
.cell-issues { display:flex; flex-direction:column; gap:2px; flex:1; overflow:hidden; }

.cell-issue-chip {
  display:flex; align-items:center; gap:4px; padding:2px 5px;
  border-radius:4px; font-size:0.65rem; cursor:pointer;
  transition:opacity 0.15s; overflow:hidden;
  white-space:nowrap;
}
.cell-issue-chip:hover { opacity:0.8; }
.cell-issue-chip.type-task  { background:rgba(16,185,129,0.12); color:var(--accent2); }
.cell-issue-chip.type-bug   { background:rgba(255,79,106,0.12); color:var(--red); }
.cell-issue-chip.type-story { background:rgba(0,217,126,0.12);  color:var(--green); }
.cell-issue-chip.type-epic  { background:rgba(6,182,212,0.12); color:#06b6d4; }

.chip-key { font-family:var(--font-mono); font-size:0.6rem; opacity:0.7; flex-shrink:0; }
.chip-title { flex:1; overflow:hidden; text-overflow:ellipsis; }
.chip-status {
  width:5px; height:5px; border-radius:50%; flex-shrink:0;
}
.chip-status.status-done        { background:var(--green); }
.chip-status.status-in_progress { background:var(--accent); }
.chip-status.status-in_review   { background:var(--yellow); }
.chip-status.status-todo        { background:var(--text3); }
.chip-status.status-backlog     { background:var(--text3); opacity:0.5; }

.cell-more {
  font-size:0.62rem; color:var(--text3); padding:1px 5px;
  cursor:pointer; transition:color 0.15s;
}
.cell-more:hover { color:var(--accent2); }

.cal-loading { flex:1; display:flex; align-items:center; justify-content:center; gap:10px; color:var(--text3); }
.spinner {
  width:18px; height:18px; border-radius:50%;
  border:2px solid var(--border); border-top-color:var(--accent);
  animation:spin 0.7s linear infinite;
}
@keyframes spin { to { transform:rotate(360deg); } }

/* Modals */
.modal-overlay {
  position:fixed; inset:0; background:rgba(0,0,0,0.7); backdrop-filter:blur(4px);
  display:flex; align-items:center; justify-content:center; z-index:200; padding:1rem;
}
.modal {
  background:var(--bg2); border:1px solid var(--border2); border-radius:14px;
  padding:1.5rem; width:100%; max-width:480px;
  box-shadow:0 32px 64px rgba(0,0,0,0.6);
  animation:modalIn 0.2s ease;
}
.issue-modal { max-width:420px; }
@keyframes modalIn { from { opacity:0; transform:scale(0.96) translateY(8px); } to { opacity:1; transform:scale(1) translateY(0); } }
.modal-head { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:1.25rem; }
.modal-head h2 { font-family:var(--font-display); font-size:1.1rem; font-weight:700; letter-spacing:-0.02em; margin-top:4px; }
.modal-date-label { font-size:0.72rem; color:var(--text3); text-transform:uppercase; letter-spacing:0.06em; }
.modal-close { background:none; border:none; color:var(--text3); cursor:pointer; font-size:1rem; padding:4px; transition:color 0.15s; }
.modal-close:hover { color:var(--text); }

.modal-issue-list { display:flex; flex-direction:column; gap:6px; max-height:360px; overflow-y:auto; }
.modal-issue-row {
  display:flex; align-items:center; gap:10px; padding:10px 12px;
  border-radius:8px; cursor:pointer; transition:background 0.15s;
  background:var(--bg3); border:1px solid var(--border);
}
.modal-issue-row:hover { border-color:var(--border2); }
.row-type-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.dot-task  { background:var(--accent2); }
.dot-bug   { background:var(--red); }
.dot-story { background:var(--green); }
.dot-epic  { background:#06b6d4; }
.row-content { flex:1; min-width:0; }
.row-key-title { display:flex; align-items:center; gap:8px; margin-bottom:4px; }
.row-key { font-family:var(--font-mono); font-size:0.68rem; color:var(--text3); flex-shrink:0; }
.row-title { font-size:0.83rem; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.row-badges { display:flex; gap:5px; }
.modal-empty { font-size:0.83rem; color:var(--text3); text-align:center; padding:1.5rem; }

.issue-modal-body { display:flex; flex-direction:column; gap:0; margin-bottom:1.25rem; }
.issue-modal-row {
  display:flex; align-items:center; padding:9px 0;
  border-bottom:1px solid var(--border);
}
.issue-modal-row:last-child { border-bottom:none; }
.im-label { font-size:0.72rem; text-transform:uppercase; letter-spacing:0.06em; color:var(--text3); width:80px; flex-shrink:0; }
.im-val { font-size:0.85rem; color:var(--text); display:flex; align-items:center; gap:6px; }
.mono { font-family:var(--font-mono); font-size:0.78rem; }
.modal-actions { display:flex; gap:8px; justify-content:flex-end; }

/* Badges */
.badge-pill { font-size:0.65rem; padding:2px 7px; border-radius:4px; font-weight:500; }
.priority-critical { background:rgba(255,79,106,0.12); color:var(--red); }
.priority-high     { background:rgba(255,140,66,0.12); color:var(--orange); }
.priority-medium   { background:rgba(255,209,102,0.12); color:var(--yellow); }
.priority-low      { background:rgba(100,180,255,0.12); color:#64b4ff; }
.status-pill-done        { background:rgba(0,217,126,0.12); color:var(--green); }
.status-pill-in_progress { background:rgba(16,185,129,0.12); color:var(--accent2); }
.status-pill-in_review   { background:rgba(255,209,102,0.12); color:var(--yellow); }
.status-pill-todo        { background:rgba(255,255,255,0.06); color:var(--text2); }
.status-pill-backlog     { background:rgba(255,255,255,0.04); color:var(--text3); }
.type-badge-sm { font-size:0.72rem; padding:2px 7px; border-radius:4px; font-weight:500; }
.type-task  { background:rgba(16,185,129,0.12); color:var(--accent2); }
.type-bug   { background:rgba(255,79,106,0.12); color:var(--red); }
.type-story { background:rgba(0,217,126,0.12); color:var(--green); }
.type-epic  { background:rgba(6,182,212,0.12); color:#06b6d4; }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .sidebar { display: none; }
  .cal-cell { min-height: 70px; }
}
@media (max-width: 640px) {
  .cal-grid { grid-template-columns: repeat(7, minmax(40px, 1fr)); }
  .cal-cell { min-height: 50px; padding: 2px; }
  .cell-issue-chip { font-size: 0.58rem; padding: 1px 3px; }
  .cal-header { flex-direction: column; gap: 8px; align-items: flex-start; }
  .cal-main { padding: 1rem; }
}
</style>
