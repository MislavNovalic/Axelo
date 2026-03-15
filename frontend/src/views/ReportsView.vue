<template>
  <div class="app-shell">
    <Navbar />
    <div class="shell-body">
      <aside class="sidebar">
        <router-link to="/" class="sidebar-item"><span class="icon">⬛</span> Overview</router-link>
        <router-link :to="`/projects/${projectId}`" class="sidebar-item"><span class="icon">📌</span> Board</router-link>
        <router-link :to="`/projects/${projectId}/backlog`" class="sidebar-item"><span class="icon">📋</span> Backlog</router-link>
        <router-link :to="`/projects/${projectId}/team`" class="sidebar-item"><span class="icon">👥</span> Team</router-link>
        <div class="sidebar-item active"><span class="icon">📊</span> Reports</div>
      </aside>

      <main class="content">
        <div class="page-header anim-fade-down">
          <div>
            <h1 class="page-title">Reports</h1>
            <p class="page-sub">{{ project?.name }} · Analytics & Insights</p>
          </div>
          <!-- Sprint selector for burndown -->
          <select v-model="selectedSprintId" class="sprint-select">
            <option v-for="s in sprints" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </div>

        <!-- Tabs -->
        <div class="report-tabs anim-slide-up" style="--delay:0.05s">
          <button v-for="tab in tabs" :key="tab.id"
            :class="['tab-btn', { active: activeTab === tab.id }]"
            @click="activeTab = tab.id">
            {{ tab.icon }} {{ tab.label }}
          </button>
        </div>

        <!-- ── Burndown ── -->
        <div v-if="activeTab === 'burndown'" class="report-card anim-slide-up" style="--delay:0.1s">
          <div class="card-header">
            <h2>Sprint Burndown</h2>
            <div class="legend">
              <span class="legend-item"><span class="dot" style="background:#10b981"></span> Ideal</span>
              <span class="legend-item"><span class="dot" style="background:#00d97e"></span> Actual</span>
            </div>
          </div>
          <div v-if="burndownLoading" class="chart-skeleton"></div>
          <svg v-else-if="burndown" class="chart-svg" :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="none">
            <!-- Grid lines -->
            <line v-for="i in 5" :key="i" :x1="PAD" :x2="W-PAD/2"
              :y1="PAD + ((H-PAD*2)/(5))*(i-1)" :y2="PAD + ((H-PAD*2)/(5))*(i-1)"
              stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
            <!-- Ideal line -->
            <polyline :points="idealPoints" fill="none" stroke="#10b981" stroke-width="2" stroke-dasharray="6 3" opacity="0.7"/>
            <!-- Actual line -->
            <polyline :points="actualPoints" fill="none" stroke="#00d97e" stroke-width="2.5"/>
            <!-- Actual area -->
            <polygon :points="actualArea" fill="rgba(0,217,126,0.07)"/>
            <!-- Dots -->
            <circle v-for="pt in actualPts" :key="pt.date" :cx="pt.x" :cy="pt.y" r="3.5" fill="#00d97e"/>
            <!-- Labels -->
            <text v-for="pt in labeledIdealPts"
              :key="pt.date" :x="pt.x" :y="H-4" font-size="10" fill="rgba(144,144,176,0.7)" text-anchor="middle">
              {{ pt.date.slice(5) }}
            </text>
          </svg>
          <div v-else class="no-data">Select a sprint with start/end dates to see burndown</div>
          <div v-if="burndown" class="burndown-stats">
            <div class="bstat"><span class="bstat-val">{{ burndown.total_points }}</span><span class="bstat-label">Total Points</span></div>
            <div class="bstat"><span class="bstat-val" style="color:var(--green)">{{ burndown.done_points }}</span><span class="bstat-label">Completed</span></div>
            <div class="bstat"><span class="bstat-val" style="color:var(--orange)">{{ burndown.total_points - burndown.done_points }}</span><span class="bstat-label">Remaining</span></div>
          </div>
        </div>

        <!-- ── Velocity ── -->
        <div v-if="activeTab === 'velocity'" class="report-card anim-slide-up" style="--delay:0.1s">
          <div class="card-header">
            <h2>Team Velocity</h2>
            <div v-if="velocity" class="metric-chip">Avg: {{ velocity.avg_velocity }} pts/sprint</div>
          </div>
          <div v-if="velocityLoading" class="chart-skeleton"></div>
          <div v-else-if="velocity?.sprints?.length" class="bar-chart">
            <div v-for="s in velocity.sprints" :key="s.sprint_id" class="bar-group">
              <div class="bar-labels">
                <span class="bar-label-val committed">{{ s.committed }}</span>
                <span class="bar-label-val completed" style="color:var(--green)">{{ s.completed }}</span>
              </div>
              <div class="bars">
                <div class="bar committed-bar" :style="`height:${barH(s.committed)}px`" title="Committed"></div>
                <div class="bar completed-bar" :style="`height:${barH(s.completed)}px`" title="Completed"></div>
              </div>
              <div class="bar-name">{{ s.sprint_name.replace('Sprint ','S') }}</div>
            </div>
          </div>
          <div v-else class="no-data">No completed sprints yet</div>
        </div>

        <!-- ── Cycle Time ── -->
        <div v-if="activeTab === 'cycle-time'" class="report-card anim-slide-up" style="--delay:0.1s">
          <div class="card-header">
            <h2>Cycle Time</h2>
            <div v-if="cycleTime" class="metric-chip">Avg: {{ cycleTime.avg_days }} days</div>
          </div>
          <div v-if="cycleLoading" class="chart-skeleton"></div>
          <div v-else-if="cycleTime?.issues?.length" class="cycle-list">
            <div v-for="i in cycleTime.issues.slice(0,20)" :key="i.key" class="cycle-row">
              <span class="cycle-dot" :class="`type-${i.type}`"></span>
              <span class="cycle-key">{{ i.key }}</span>
              <span class="cycle-title">{{ i.title }}</span>
              <div class="cycle-bar-wrap">
                <div class="cycle-bar" :style="`width:${Math.min(i.days/30*100,100)}%; background:${cycleColor(i.days)}`"></div>
              </div>
              <span class="cycle-days">{{ i.days }}d</span>
            </div>
          </div>
          <div v-else class="no-data">No completed issues yet</div>
        </div>

        <!-- ── Issue Flow ── -->
        <div v-if="activeTab === 'flow'" class="report-card anim-slide-up" style="--delay:0.1s">
          <div class="card-header">
            <h2>Issue Flow <span style="font-size:0.75rem;font-weight:400;color:var(--text3)">(last 30 days)</span></h2>
            <div class="legend">
              <span class="legend-item"><span class="dot" style="background:#10b981"></span> Created</span>
              <span class="legend-item"><span class="dot" style="background:#00d97e"></span> Resolved</span>
            </div>
          </div>
          <div v-if="flowLoading" class="chart-skeleton"></div>
          <svg v-else-if="flow" class="chart-svg" :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="none">
            <line v-for="i in 4" :key="i" :x1="PAD" :x2="W-PAD/2"
              :y1="PAD + ((H-PAD*2)/4)*(i-1)" :y2="PAD + ((H-PAD*2)/4)*(i-1)"
              stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
            <polyline :points="flowCreatedPoints" fill="none" stroke="#10b981" stroke-width="2"/>
            <polyline :points="flowResolvedPoints" fill="none" stroke="#00d97e" stroke-width="2"/>
          </svg>
        </div>

        <!-- ── Audit Log ── -->
        <div v-if="activeTab === 'audit'" class="report-card anim-slide-up" style="--delay:0.1s">
          <div class="card-header"><h2>Audit Log</h2></div>
          <div v-if="auditLoading" class="chart-skeleton"></div>
          <div v-else-if="auditLog.length" class="audit-list">
            <div v-for="entry in auditLog" :key="entry.id" class="audit-row">
              <div class="audit-avatar">{{ entry.user?.full_name?.[0]?.toUpperCase() || '?' }}</div>
              <div class="audit-body">
                <span class="audit-actor">{{ entry.user?.full_name || 'System' }}</span>
                <span class="audit-action" :class="`action-${entry.action}`">{{ entry.action }}</span>
                <span v-if="entry.entity_key" class="audit-key">{{ entry.entity_key }}</span>
                <span v-if="entry.description" class="audit-desc">{{ entry.description }}</span>
                <div v-if="entry.diff && Object.keys(entry.diff).length" class="audit-diff">
                  <span v-for="(vals, field) in entry.diff" :key="field" class="diff-chip">
                    {{ field }}: <del>{{ vals[0] ?? '—' }}</del> → <ins>{{ vals[1] ?? '—' }}</ins>
                  </span>
                </div>
              </div>
              <div class="audit-time">{{ timeAgo(entry.created_at) }}</div>
            </div>
          </div>
          <div v-else class="no-data">No activity recorded yet</div>
        </div>

      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { formatDistanceToNow } from 'date-fns'
import Navbar from '@/components/Navbar.vue'
import { useProjectsStore } from '@/store/projects'
import { reportsApi, sprintsApi } from '@/api'

const route = useRoute()
const projectsStore = useProjectsStore()
const projectId = computed(() => Number(route.params.id))
const project = computed(() => projectsStore.currentProject)

const W = 700; const H = 220; const PAD = 36

const tabs = [
  { id: 'burndown',  icon: '📉', label: 'Burndown' },
  { id: 'velocity',  icon: '⚡', label: 'Velocity' },
  { id: 'cycle-time',icon: '🔄', label: 'Cycle Time' },
  { id: 'flow',      icon: '📈', label: 'Issue Flow' },
  { id: 'audit',     icon: '🗒', label: 'Audit Log' },
]
const activeTab = ref('burndown')

// Sprints
const sprints = ref([])
const selectedSprintId = ref(null)

// Data
const burndown = ref(null); const burndownLoading = ref(false)
const velocity = ref(null); const velocityLoading = ref(false)
const cycleTime = ref(null); const cycleLoading = ref(false)
const flow = ref(null); const flowLoading = ref(false)
const auditLog = ref([]); const auditLoading = ref(false)

onMounted(async () => {
  if (!projectsStore.currentProject || projectsStore.currentProject.id !== projectId.value) {
    await projectsStore.fetchProject(projectId.value)
  }
  const r = await sprintsApi.list(projectId.value)
  sprints.value = r.data
  const active = r.data.find(s => s.status === 'active') || r.data[0]
  if (active) selectedSprintId.value = active.id
  loadAll()
})

async function loadAll() {
  loadBurndown()
  if (activeTab.value === 'velocity')  loadVelocity()
  if (activeTab.value === 'cycle-time') loadCycleTime()
  if (activeTab.value === 'flow')      loadFlow()
  if (activeTab.value === 'audit')     loadAudit()
}

watch(activeTab, (t) => {
  if (t === 'velocity'   && !velocity.value)  loadVelocity()
  if (t === 'cycle-time' && !cycleTime.value) loadCycleTime()
  if (t === 'flow'       && !flow.value)      loadFlow()
  if (t === 'audit'      && !auditLog.value.length) loadAudit()
})

watch(selectedSprintId, () => loadBurndown())

async function loadBurndown() {
  if (!selectedSprintId.value) return
  burndownLoading.value = true
  try { burndown.value = (await reportsApi.burndown(projectId.value, selectedSprintId.value)).data }
  finally { burndownLoading.value = false }
}
async function loadVelocity() {
  velocityLoading.value = true
  try { velocity.value = (await reportsApi.velocity(projectId.value)).data }
  finally { velocityLoading.value = false }
}
async function loadCycleTime() {
  cycleLoading.value = true
  try { cycleTime.value = (await reportsApi.cycleTime(projectId.value)).data }
  finally { cycleLoading.value = false }
}
async function loadFlow() {
  flowLoading.value = true
  try { flow.value = (await reportsApi.issueFlow(projectId.value)).data }
  finally { flowLoading.value = false }
}
async function loadAudit() {
  auditLoading.value = true
  try { auditLog.value = (await reportsApi.auditLog(projectId.value)).data }
  finally { auditLoading.value = false }
}

// ── Chart helpers ─────────────────────────────────────────────────────────────
function toSvgPts(data, yKey) {
  if (!data?.length) return { pts: [], points: '', area: '' }
  const maxY = Math.max(...data.map(d => d[yKey]), 1)
  const pts = data.map((d, i) => ({
    ...d,
    x: PAD + (i / Math.max(data.length - 1, 1)) * (W - PAD * 1.5),
    y: PAD + (1 - d[yKey] / maxY) * (H - PAD * 2),
  }))
  const points = pts.map(p => `${p.x},${p.y}`).join(' ')
  const area = `${pts[0].x},${H-PAD} ` + pts.map(p => `${p.x},${p.y}`).join(' ') + ` ${pts[pts.length-1].x},${H-PAD}`
  return { pts, points, area }
}

const idealPts    = computed(() => burndown.value ? toSvgPts(burndown.value.ideal,  'points').pts    : [])
const actualPts   = computed(() => burndown.value ? toSvgPts(burndown.value.actual, 'points').pts    : [])
const idealPoints = computed(() => burndown.value ? toSvgPts(burndown.value.ideal,  'points').points : '')
const labeledIdealPts = computed(() => {
  const pts = idealPts.value
  const step = Math.max(1, Math.floor(pts.length / 6))
  return pts.filter((_, idx) => idx % step === 0)
})
const actualPoints= computed(() => burndown.value ? toSvgPts(burndown.value.actual, 'points').points : '')
const actualArea  = computed(() => burndown.value ? toSvgPts(burndown.value.actual, 'points').area   : '')

const flowCreatedPoints  = computed(() => flow.value ? toSvgPts(flow.value.days, 'created').points  : '')
const flowResolvedPoints = computed(() => flow.value ? toSvgPts(flow.value.days, 'resolved').points : '')

const maxVelocity = computed(() => velocity.value ? Math.max(...velocity.value.sprints.map(s => s.committed), 1) : 1)
const BAR_MAX_H = 120
function barH(v) { return Math.max((v / maxVelocity.value) * BAR_MAX_H, 4) }
function cycleColor(d) { return d <= 3 ? '#00d97e' : d <= 7 ? '#ffd166' : '#ff4f6a' }
function timeAgo(iso) { try { return formatDistanceToNow(new Date(iso), { addSuffix: true }) } catch { return '' } }
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; min-height: 100vh; background: var(--bg); }
.shell-body { display: flex; flex: 1; overflow: hidden; height: calc(100vh - 52px); }
.sidebar { width: 210px; flex-shrink: 0; background: var(--bg2); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding: 1rem 0.75rem; gap: 2px; }
.sidebar-item { display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 7px; font-size: 0.84rem; color: var(--text2); cursor: pointer; transition: all 0.15s; text-decoration: none; }
.sidebar-item:hover { background: rgba(255,255,255,0.05); color: var(--text); }
.sidebar-item.active { background: rgba(16,185,129,0.15); color: var(--accent2); }
.icon { font-size: 0.9rem; width: 18px; text-align: center; }
.content { flex: 1; overflow-y: auto; padding: 1.75rem 2rem; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.25rem; }
.page-title { font-family: var(--font-display); font-size: 1.5rem; font-weight: 700; color: var(--text); }
.page-sub { font-size: 0.85rem; color: var(--text2); margin-top: 3px; }

.sprint-select {
  background: var(--bg2); border: 1px solid var(--border2); color: var(--text);
  padding: 6px 12px; border-radius: 8px; font-size: 0.82rem; cursor: pointer;
  font-family: var(--font-body); outline: none;
}

.report-tabs { display: flex; gap: 4px; margin-bottom: 1.25rem; flex-wrap: wrap; }
.tab-btn {
  padding: 7px 14px; border-radius: 8px; border: 1px solid var(--border);
  background: none; color: var(--text2); font-size: 0.82rem; cursor: pointer;
  font-family: var(--font-body); transition: all 0.15s;
}
.tab-btn:hover { border-color: var(--border2); color: var(--text); }
.tab-btn.active { background: rgba(16,185,129,0.15); border-color: rgba(16,185,129,0.4); color: var(--accent2); }

.report-card {
  background: var(--bg2); border: 1px solid var(--border); border-radius: 12px;
  padding: 1.5rem; margin-bottom: 1.25rem;
}
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.25rem; }
.card-header h2 { font-size: 0.95rem; font-weight: 700; color: var(--text); }
.metric-chip { background: rgba(16,185,129,0.12); color: var(--accent2); font-size: 0.78rem; font-weight: 600; padding: 4px 10px; border-radius: 8px; }
.legend { display: flex; gap: 12px; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 0.75rem; color: var(--text2); }
.dot { width: 8px; height: 8px; border-radius: 50%; }

.chart-svg { width: 100%; height: 220px; }
.chart-skeleton { height: 220px; background: var(--bg3); border-radius: 8px; animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:.4} 50%{opacity:.8} }
.no-data { text-align: center; padding: 3rem 1rem; color: var(--text2); font-size: 0.85rem; }

.burndown-stats { display: flex; gap: 2rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border); }
.bstat { display: flex; flex-direction: column; gap: 2px; }
.bstat-val { font-family: var(--font-display); font-size: 1.5rem; font-weight: 800; color: var(--text); }
.bstat-label { font-size: 0.72rem; color: var(--text3); }

/* Velocity bar chart */
.bar-chart { display: flex; align-items: flex-end; gap: 20px; height: 160px; padding: 0 1rem; }
.bar-group { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.bar-labels { display: flex; gap: 4px; font-size: 0.68rem; }
.bar-label-val { font-family: var(--font-mono); }
.committed { color: var(--text3); }
.bars { display: flex; align-items: flex-end; gap: 3px; }
.bar { width: 18px; border-radius: 3px 3px 0 0; transition: height 0.5s ease; }
.committed-bar { background: rgba(16,185,129,0.3); }
.completed-bar { background: #00d97e; }
.bar-name { font-size: 0.65rem; color: var(--text3); white-space: nowrap; }

/* Cycle time */
.cycle-list { display: flex; flex-direction: column; gap: 6px; }
.cycle-row { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid var(--border); }
.cycle-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.type-bug   { background: var(--red); }
.type-story { background: var(--green); }
.type-task  { background: var(--accent2); }
.type-epic  { background: #06b6d4; }
.cycle-key { font-family: var(--font-mono); font-size: 0.68rem; color: var(--text3); flex-shrink: 0; width: 56px; }
.cycle-title { flex: 1; font-size: 0.8rem; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cycle-bar-wrap { width: 120px; height: 6px; background: var(--bg3); border-radius: 3px; overflow: hidden; flex-shrink: 0; }
.cycle-bar { height: 100%; border-radius: 3px; }
.cycle-days { font-family: var(--font-mono); font-size: 0.72rem; color: var(--text2); width: 28px; text-align: right; flex-shrink: 0; }

/* Audit log */
.audit-list { display: flex; flex-direction: column; gap: 2px; }
.audit-row { display: flex; align-items: flex-start; gap: 10px; padding: 10px 8px; border-radius: 8px; transition: background 0.1s; }
.audit-row:hover { background: rgba(255,255,255,0.03); }
.audit-avatar { width: 28px; height: 28px; border-radius: 50%; background: var(--accent); color: #fff; font-size: 0.68rem; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.audit-body { flex: 1; font-size: 0.8rem; }
.audit-actor { font-weight: 600; color: var(--text); margin-right: 5px; }
.audit-action { font-size: 0.7rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; margin-right: 5px; text-transform: uppercase; }
.action-created  { background: rgba(0,217,126,0.12); color: var(--green); }
.action-updated  { background: rgba(16,185,129,0.12); color: var(--accent2); }
.action-deleted  { background: rgba(255,79,106,0.12); color: var(--red); }
.audit-key { font-family: var(--font-mono); font-size: 0.7rem; color: var(--text3); margin-right: 6px; }
.audit-desc { color: var(--text2); }
.audit-diff { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px; }
.diff-chip { font-size: 0.68rem; background: var(--bg3); padding: 1px 6px; border-radius: 4px; color: var(--text2); }
del { color: var(--red); text-decoration: line-through; }
ins { color: var(--green); text-decoration: none; }
.audit-time { font-size: 0.68rem; color: var(--text3); flex-shrink: 0; }

/* Animations */
.anim-fade-down { animation: fadeDown 0.5s cubic-bezier(0.22,1,0.36,1) both; }
.anim-slide-up { opacity:0; animation: slideUp 0.45s cubic-bezier(0.22,1,0.36,1) forwards; animation-delay: var(--delay,0s); }
@keyframes fadeDown { from{opacity:0;transform:translateY(-14px)} to{opacity:1;transform:translateY(0)} }
@keyframes slideUp  { from{opacity:0;transform:translateY(18px)}  to{opacity:1;transform:translateY(0)} }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .sidebar { display: none; }
  .burndown-stats { flex-wrap: wrap; gap: 1rem; }
}
@media (max-width: 640px) {
  .content { padding: 1rem; }
  .report-tabs { flex-wrap: wrap; }
  .chart-svg { overflow-x: auto; }
  .page-header { flex-direction: column; align-items: flex-start; gap: 8px; }
  .bar-chart { overflow-x: auto; }
}
</style>
