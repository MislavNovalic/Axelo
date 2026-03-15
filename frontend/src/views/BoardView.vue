<template>
  <div class="app-shell">
    <Navbar @new-issue="showCreate = true" />
    <div class="shell-body">
      <main class="content">
        <div class="board-header">
          <div>
            <h1 class="board-title">Board</h1>
            <p v-if="activeSprint" class="board-sub">
              <span class="sprint-tag">{{ activeSprint.name }}</span>
              {{ activeSprint.goal }}
            </p>
            <p v-else class="board-sub">Showing all open issues</p>
          </div>
          <button class="btn-primary" @click="showCreate = true">+ Issue</button>
        </div>

        <div class="board-columns">
          <div
            v-for="col in columns" :key="col.status"
            class="board-col"
            @dragover.prevent
            @drop="onDrop($event, col.status)"
            @dragenter.prevent="dragOver = col.status"
            @dragleave="dragOver = null"
            :class="{ 'drag-over': dragOver === col.status }"
          >
            <div class="col-header">
              <div class="col-dot" :style="`background:${col.color}`"></div>
              <span class="col-name">{{ col.label }}</span>
              <span class="col-count">{{ issuesByStatus(col.status).length }}</span>
            </div>
            <div class="col-body">
              <div
                v-for="issue in issuesByStatus(col.status)"
                :key="issue.id"
                :class="{ 'rt-flash': flashIds.has(issue.id) }"
              >
                <IssueCard
                  :issue="issue"
                  @click="openIssue(issue)"
                  @dragstart="draggedIssue = $event"
                />
              </div>
              <div v-if="!issuesByStatus(col.status).length" class="col-empty">
                <div class="col-empty-icon">{{ col.emptyIcon }}</div>
                <div>{{ col.emptyText }}</div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>

    <CreateIssueModal
      v-if="showCreate"
      :project-id="projectId"
      :sprints="sprints"
      :default-sprint-id="activeSprint?.id ?? null"
      @close="showCreate = false"
      @created="loadIssues"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import IssueCard from '@/components/IssueCard.vue'
import CreateIssueModal from '@/components/CreateIssueModal.vue'
import { useProjectsStore } from '@/store/projects'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { useIssuesStore } from '@/store/issues'
import { useWsStore } from '@/store/ws'
import { sprintsApi } from '@/api'

const route = useRoute()
const router = useRouter()
const projectsStore = useProjectsStore()
const issuesStore = useIssuesStore()
const wsStore = useWsStore()
const projectId = computed(() => Number(route.params.id))
const showCreate = ref(false)
const draggedIssue = ref(null)
const dragOver = ref(null)
const sprints = ref([])
const activeSprint = computed(() => sprints.value.find(s => s.status === 'active'))

// Flash set — issue IDs that were just updated remotely
const flashIds = ref(new Set())
function flashIssue(id) {
  flashIds.value = new Set([...flashIds.value, id])
  setTimeout(() => {
    flashIds.value = new Set([...flashIds.value].filter(x => x !== id))
  }, 1200)
}

const columns = [
  { status: 'todo',        label: 'To Do',      color: '#4a6455', emptyIcon: '○', emptyText: 'Nothing queued' },
  { status: 'in_progress', label: 'In Progress', color: 'var(--accent)', emptyIcon: '◐', emptyText: 'No work in progress' },
  { status: 'in_review',   label: 'In Review',  color: 'var(--yellow)', emptyIcon: '◑', emptyText: 'Nothing in review' },
  { status: 'done',        label: 'Done',        color: 'var(--green)', emptyIcon: '●', emptyText: 'No completed items' },
]

const issuesByStatus = (s) => issuesStore.issues.filter(i => i.status === s)
const doneCount = computed(() => issuesByStatus('done').length)
const totalCount = computed(() => issuesStore.issues.filter(i => i.status !== 'backlog').length)
const sprintProgress = computed(() => totalCount.value ? Math.round((doneCount.value / totalCount.value) * 100) : 0)

async function loadIssues() {
  const active = activeSprint.value
  await issuesStore.fetchIssues(projectId.value, active ? { sprint_id: active.id } : {})
}

// ── Real-time handlers ──────────────────────────────────────────────────────
function onIssueCreated(data) {
  if (issuesStore.issues.find(i => i.id === data.id)) return
  // Only show on board if it belongs to the active sprint (or no sprint filter)
  const active = activeSprint.value
  if (active && data.sprint_id !== active.id) return
  if (!active && data.status === 'backlog') return
  issuesStore.issues.push(data)
  flashIssue(data.id)
}
function onIssueUpdated(data) {
  const idx = issuesStore.issues.findIndex(i => i.id === data.id)
  if (idx !== -1) {
    issuesStore.issues[idx] = { ...issuesStore.issues[idx], ...data }
    flashIssue(data.id)
  }
}
function onIssueDeleted({ id }) {
  issuesStore.issues = issuesStore.issues.filter(i => i.id !== id)
}
function onSprintUpdated(data) {
  const idx = sprints.value.findIndex(s => s.id === data.id)
  if (idx !== -1) sprints.value[idx] = { ...sprints.value[idx], ...data }
}

// Keyboard shortcut: C → create issue
useKeyboardShortcuts({ onCreateIssue: () => { showCreate.value = true } })

onMounted(async () => {
  await projectsStore.fetchProject(projectId.value)
  const r = await sprintsApi.list(projectId.value)
  sprints.value = r.data
  await loadIssues()

  // Join project WS room
  wsStore.connect(projectId.value)
  wsStore.on('issue_created',  onIssueCreated)
  wsStore.on('issue_updated',  onIssueUpdated)
  wsStore.on('issue_deleted',  onIssueDeleted)
  wsStore.on('sprint_updated', onSprintUpdated)
})

onBeforeUnmount(() => {
  wsStore.off('issue_created',  onIssueCreated)
  wsStore.off('issue_updated',  onIssueUpdated)
  wsStore.off('issue_deleted',  onIssueDeleted)
  wsStore.off('sprint_updated', onSprintUpdated)
  // Reconnect without project room (keep notification WS alive)
  wsStore.connect(null)
})

async function onDrop(event, newStatus) {
  dragOver.value = null
  if (!draggedIssue.value || draggedIssue.value.status === newStatus) return
  await issuesStore.updateIssue(projectId.value, draggedIssue.value.id, { status: newStatus })
  draggedIssue.value = null
}

function openIssue(issue) { router.push(`/projects/${projectId.value}/issues/${issue.id}`) }
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; min-height: 100vh; background: var(--bg); }
.shell-body { display: flex; flex: 1; overflow: hidden; height: calc(100vh - 52px); }

.content { flex: 1; overflow-x: auto; padding: 1.5rem; display: flex; flex-direction: column; }
.board-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.25rem; flex-shrink: 0; }
.board-title { font-family: var(--font-display); font-size: 1.3rem; font-weight: 700; letter-spacing: -0.02em; color: var(--text); }
.board-sub { font-size: 0.82rem; color: var(--text2); margin-top: 3px; display: flex; align-items: center; gap: 6px; }
.sprint-tag { background: rgba(0,217,126,0.1); color: var(--green); font-size: 0.72rem; font-weight: 600; padding: 2px 8px; border-radius: 4px; }

.board-columns { display: flex; gap: 12px; flex: 1; min-width: max-content; align-items: flex-start; }
.board-col { width: 280px; flex-shrink: 0; display: flex; flex-direction: column; }
.col-header { display: flex; align-items: center; gap: 7px; margin-bottom: 10px; }
.col-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.col-name { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; color: var(--text2); }
.col-count { font-size: 0.65rem; color: var(--text3); background: var(--bg2); padding: 1px 7px; border-radius: 100px; margin-left: 2px; }
.col-body { display: flex; flex-direction: column; gap: 7px; min-height: 120px; background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 8px; transition: background 0.15s, border-color 0.15s; }
.board-col.drag-over .col-body { background: rgba(16,185,129,0.06); border-color: rgba(16,185,129,0.4); }
.col-empty { font-size: 0.75rem; color: var(--text3); text-align: center; padding: 20px 0; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.col-empty-icon { font-size: 1.2rem; opacity: 0.3; }

.btn-primary { padding: 8px 16px; border-radius: 8px; background: var(--accent); color: #fff; border: none; cursor: pointer; font-size: 0.83rem; font-weight: 600; font-family: var(--font-body); transition: opacity 0.15s; }
.btn-primary:hover { opacity: 0.88; }

/* ── Real-time flash highlight ──────────────────────────────────────────── */
.rt-flash { animation: rtFlash 1.2s ease; border-radius: 8px; }
@keyframes rtFlash {
  0%   { box-shadow: 0 0 0 2px rgba(16,185,129,0.8), 0 0 16px rgba(16,185,129,0.4); }
  60%  { box-shadow: 0 0 0 2px rgba(16,185,129,0.3); }
  100% { box-shadow: none; }
}

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .board-col { width: 240px; }
}
@media (max-width: 640px) {
  .board-col { width: 200px; }
  .content { padding: 1rem; }
  .board-header { flex-direction: column; align-items: flex-start; gap: 8px; }
}
</style>