<template>
  <div class="roadmap-page">
    <div class="roadmap-header">
      <div>
        <h1 class="page-title">Roadmap</h1>
        <p class="page-sub">{{ project?.name }} · Timeline view across sprints and epics</p>
      </div>
      <div class="header-controls">
        <select v-model="viewMode" class="view-select">
          <option value="sprints">By Sprint</option>
          <option value="epics">By Epic</option>
          <option value="all">All Issues</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading-state">Loading roadmap…</div>

    <div v-else-if="error" class="error-state">{{ error }}</div>

    <div v-else class="roadmap-content">
      <!-- Sprint swimlanes -->
      <div v-if="viewMode === 'sprints'" class="sprint-lanes">
        <div v-if="!roadmapData.sprints?.length" class="empty-state">
          No sprints yet. Create sprints in the Backlog view.
        </div>
        <div v-for="sprint in roadmapData.sprints" :key="sprint.id" class="sprint-lane">
          <div class="lane-header">
            <span class="sprint-dot" :class="sprint.status"></span>
            <strong class="sprint-name">{{ sprint.name }}</strong>
            <span class="sprint-status-badge" :class="sprint.status">{{ sprint.status }}</span>
            <span v-if="sprint.start_date" class="sprint-dates">
              {{ fmtDate(sprint.start_date) }} → {{ fmtDate(sprint.end_date) }}
            </span>
          </div>
          <div class="lane-issues">
            <div v-for="issue in issuesBySprint(sprint.id)" :key="issue.id"
              class="issue-bar" :class="[issue.type, issue.status]"
              @click="$router.push(`/projects/${projectId}/issues/${issue.id}`)">
              <span class="bar-key">{{ issue.key }}</span>
              <span class="bar-title">{{ issue.title }}</span>
              <span class="bar-pts" v-if="issue.story_points">{{ issue.story_points }}pt</span>
              <span class="bar-status" :class="issue.status">{{ labelStatus(issue.status) }}</span>
            </div>
          </div>
        </div>
        <!-- Unscheduled -->
        <div class="sprint-lane unscheduled">
          <div class="lane-header">
            <span class="sprint-name">Unscheduled</span>
          </div>
          <div class="lane-issues">
            <div v-for="issue in unscheduled" :key="issue.id"
              class="issue-bar" :class="[issue.type, issue.status]"
              @click="$router.push(`/projects/${projectId}/issues/${issue.id}`)">
              <span class="bar-key">{{ issue.key }}</span>
              <span class="bar-title">{{ issue.title }}</span>
              <span class="bar-status" :class="issue.status">{{ labelStatus(issue.status) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Epic swimlanes -->
      <div v-else-if="viewMode === 'epics'" class="epic-lanes">
        <div v-if="!roadmapData.epics?.length" class="empty-state">
          No epics yet. Create an epic-type issue in the board or backlog.
        </div>
        <div v-for="epic in roadmapData.epics" :key="epic.id" class="epic-lane">
          <div class="lane-header epic-lane-header"
            @click="$router.push(`/projects/${projectId}/issues/${epic.id}`)">
            <span class="epic-icon">⚡</span>
            <strong class="epic-name">{{ epic.key }} · {{ epic.title }}</strong>
            <span class="bar-status" :class="epic.status">{{ labelStatus(epic.status) }}</span>
            <span v-if="epic.story_points" class="epic-pts">{{ epic.story_points }}pt</span>
          </div>
          <div class="children-list">
            <div v-for="child in epic.children" :key="child.id"
              class="child-row" :class="child.status"
              @click="$router.push(`/projects/${projectId}/issues/${child.id}`)">
              <span class="child-type-icon">{{ typeIcon(child.type) }}</span>
              <span class="child-key">{{ child.key }}</span>
              <span class="child-title">{{ child.title }}</span>
              <span class="bar-status" :class="child.status">{{ labelStatus(child.status) }}</span>
              <span v-if="child.start_date" class="child-dates">
                {{ fmtDate(child.start_date) }}{{ child.end_date ? ' → ' + fmtDate(child.end_date) : '' }}
              </span>
            </div>
            <div v-if="!epic.children.length" class="no-children">No stories linked to this epic.</div>
          </div>
        </div>
      </div>

      <!-- All issues flat list -->
      <div v-else class="all-issues">
        <div class="issue-table-header">
          <span>Key</span><span>Title</span><span>Type</span><span>Status</span><span>Sprint</span><span>Points</span>
        </div>
        <div v-for="issue in allIssues" :key="issue.id"
          class="issue-table-row"
          @click="$router.push(`/projects/${projectId}/issues/${issue.id}`)">
          <span class="key-col">{{ issue.key }}</span>
          <span class="title-col">{{ issue.title }}</span>
          <span class="type-badge" :class="issue.type">{{ issue.type }}</span>
          <span class="bar-status" :class="issue.status">{{ labelStatus(issue.status) }}</span>
          <span class="sprint-col">{{ sprintName(issue.sprint_id) }}</span>
          <span class="pts-col">{{ issue.story_points ?? '—' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { roadmapApi, projectsApi } from '@/api'

const route = useRoute()
const projectId = parseInt(route.params.id)

const project = ref(null)
const roadmapData = ref({ epics: [], unparented: [], sprints: [] })
const loading = ref(true)
const error = ref('')
const viewMode = ref('sprints')

const sprintMap = computed(() => {
  const m = {}
  for (const sp of roadmapData.value.sprints || []) m[sp.id] = sp
  return m
})

const allIssues = computed(() => {
  const epics = roadmapData.value.epics || []
  const children = epics.flatMap(e => e.children || [])
  const unparented = roadmapData.value.unparented || []
  return [...epics, ...children, ...unparented]
})

const unscheduled = computed(() =>
  allIssues.value.filter(i => !i.sprint_id)
)

function issuesBySprint(sprintId) {
  return allIssues.value.filter(i => i.sprint_id === sprintId)
}

function sprintName(sprintId) {
  return sprintId ? sprintMap.value[sprintId]?.name ?? '—' : '—'
}

function fmtDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

function labelStatus(s) {
  return { backlog: 'Backlog', todo: 'To Do', in_progress: 'In Progress', in_review: 'In Review', done: 'Done' }[s] ?? s
}

function typeIcon(t) {
  return { bug: '🐛', story: '📖', task: '✅', epic: '⚡' }[t] ?? '•'
}

onMounted(async () => {
  try {
    const [projRes, roadmapRes] = await Promise.all([
      projectsApi.get(projectId),
      roadmapApi.get(projectId),
    ])
    project.value = projRes.data
    roadmapData.value = roadmapRes.data
  } catch (e) {
    error.value = 'Failed to load roadmap.'
  } finally { loading.value = false }
})
</script>

<style scoped>
.roadmap-page { padding: 2rem; max-width: 1200px; margin: 0 auto; }
.roadmap-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 2rem; gap: 1rem; }
.page-title { font-family: var(--font-display); font-size: 1.6rem; font-weight: 800; color: var(--text); margin-bottom: 0.2rem; }
.page-sub { font-size: 0.85rem; color: var(--text2); }
.view-select { padding: 8px 12px; border: 1.5px solid var(--border2); border-radius: 8px; background: var(--bg2); color: var(--text); font-size: 0.85rem; cursor: pointer; outline: none; }
.loading-state, .error-state, .empty-state { text-align: center; padding: 3rem; color: var(--text3); font-size: 0.9rem; }
.sprint-lanes, .epic-lanes { display: flex; flex-direction: column; gap: 12px; }
.sprint-lane, .epic-lane { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
.lane-header { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-bottom: 1px solid var(--border); background: var(--bg3); }
.sprint-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.sprint-dot.active { background: var(--green); }
.sprint-dot.planning { background: var(--yellow); }
.sprint-dot.completed { background: var(--text3); }
.sprint-name, .epic-name { font-size: 0.9rem; font-weight: 700; color: var(--text); }
.sprint-status-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; }
.sprint-status-badge.active { background: rgba(0,217,126,0.12); color: var(--green); }
.sprint-status-badge.planning { background: rgba(255,209,30,0.12); color: var(--yellow); }
.sprint-status-badge.completed { background: var(--bg2); color: var(--text3); }
.sprint-dates { font-size: 0.78rem; color: var(--text3); margin-left: auto; }
.lane-issues { padding: 10px; display: flex; flex-direction: column; gap: 4px; min-height: 40px; }
.issue-bar {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  border-radius: 8px; border-left: 3px solid var(--border2);
  background: var(--bg); cursor: pointer; font-size: 0.83rem;
  transition: background 0.15s, border-color 0.15s;
}
.issue-bar:hover { background: var(--bg3); border-left-color: var(--accent); }
.issue-bar.epic { border-left-color: #06b6d4; }
.issue-bar.bug { border-left-color: var(--red); }
.issue-bar.story { border-left-color: var(--green); }
.issue-bar.task { border-left-color: var(--accent2); }
.bar-key { font-family: var(--font-mono); font-size: 0.75rem; color: var(--text3); flex-shrink: 0; }
.bar-title { flex: 1; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bar-pts { font-size: 0.72rem; color: var(--text3); flex-shrink: 0; }
.bar-status { padding: 2px 7px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; flex-shrink: 0; }
.bar-status.done { background: rgba(0,217,126,0.12); color: var(--green); }
.bar-status.in_progress { background: rgba(16,185,129,0.12); color: var(--accent2); }
.bar-status.in_review { background: rgba(255,140,66,0.12); color: var(--orange); }
.bar-status.todo { background: var(--bg3); color: var(--text3); }
.bar-status.backlog { background: var(--bg3); color: var(--text3); }
.unscheduled .lane-header { background: transparent; border-bottom-color: var(--border); }
.epic-lane-header { cursor: pointer; }
.epic-lane-header:hover { background: rgba(16,185,129,0.06); }
.epic-icon { font-size: 0.9rem; }
.epic-pts { margin-left: auto; font-size: 0.78rem; color: var(--text3); }
.children-list { padding: 8px; display: flex; flex-direction: column; gap: 3px; }
.child-row { display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 7px; background: var(--bg); font-size: 0.82rem; cursor: pointer; transition: background 0.15s; }
.child-row:hover { background: var(--bg3); }
.child-type-icon { flex-shrink: 0; }
.child-key { font-family: var(--font-mono); font-size: 0.74rem; color: var(--text3); flex-shrink: 0; }
.child-title { flex: 1; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.child-dates { font-size: 0.74rem; color: var(--text3); white-space: nowrap; margin-left: auto; }
.no-children { font-size: 0.8rem; color: var(--text3); padding: 8px 10px; }
.all-issues { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
.issue-table-header { display: grid; grid-template-columns: 90px 1fr 80px 100px 120px 60px; gap: 8px; padding: 10px 16px; background: var(--bg3); border-bottom: 1px solid var(--border); font-size: 0.75rem; font-weight: 700; color: var(--text3); text-transform: uppercase; letter-spacing: 0.05em; }
.issue-table-row { display: grid; grid-template-columns: 90px 1fr 80px 100px 120px 60px; gap: 8px; padding: 9px 16px; border-bottom: 1px solid var(--border); font-size: 0.82rem; cursor: pointer; transition: background 0.12s; align-items: center; }
.issue-table-row:last-child { border-bottom: none; }
.issue-table-row:hover { background: var(--bg3); }
.key-col { font-family: var(--font-mono); font-size: 0.76rem; color: var(--text3); }
.title-col { color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.type-badge { font-size: 0.72rem; font-weight: 700; text-transform: capitalize; }
.type-badge.epic { color: #06b6d4; }
.type-badge.bug { color: var(--red); }
.type-badge.story { color: var(--green); }
.type-badge.task { color: var(--accent2); }
.sprint-col { color: var(--text3); font-size: 0.78rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pts-col { color: var(--text3); font-family: var(--font-mono); font-size: 0.78rem; text-align: center; }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .roadmap-page { padding: 1.5rem; }
  .issue-table-header,
  .issue-table-row { grid-template-columns: 80px 1fr 70px 90px; }
  .issue-table-header > :nth-child(5),
  .issue-table-header > :nth-child(6),
  .issue-table-row > :nth-child(5),
  .issue-table-row > :nth-child(6) { display: none; }
}
@media (max-width: 640px) {
  .roadmap-page { padding: 1rem; }
  .roadmap-header { flex-direction: column; gap: 0.75rem; }
  .lane-header { flex-wrap: wrap; }
  .issue-table-header,
  .issue-table-row { grid-template-columns: 70px 1fr 80px; }
  .issue-table-header > :nth-child(3),
  .issue-table-row > :nth-child(3),
  .issue-table-header > :nth-child(5),
  .issue-table-header > :nth-child(6),
  .issue-table-row > :nth-child(5),
  .issue-table-row > :nth-child(6) { display: none; }
  .bar-title { font-size: 0.78rem; }
}
</style>
