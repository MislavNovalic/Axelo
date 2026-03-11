<template>
  <div class="app-shell">
    <Navbar @new-issue="showCreate = true" />
    <div class="shell-body">
      <aside class="sidebar">
        <router-link to="/" class="sidebar-item"><span class="icon">⬛</span> Overview</router-link>
        <div class="sidebar-item active"><span class="icon">📌</span> Board</div>
        <router-link :to="`/projects/${projectId}/backlog`" class="sidebar-item"><span class="icon">📋</span> Backlog</router-link>
        <div class="sidebar-section-title">Sprint</div>
        <div v-if="activeSprint" class="sprint-info">
          <div class="sprint-badge">● ACTIVE</div>
          <div class="sprint-name">{{ activeSprint.name }}</div>
        </div>
        <div v-else class="sprint-empty">No active sprint</div>
      </aside>

      <main class="content">
        <div class="board-header">
          <div>
            <h1 class="board-title">Board</h1>
            <p v-if="activeSprint" class="board-sub">
              Sprint: <span style="color:var(--accent2);">{{ activeSprint.name }}</span>
            </p>
            <p v-else class="board-sub">All open issues</p>
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
              <IssueCard
                v-for="issue in issuesByStatus(col.status)"
                :key="issue.id"
                :issue="issue"
                @click="openIssue(issue)"
                @dragstart="draggedIssue = $event"
              />
              <div v-if="!issuesByStatus(col.status).length" class="col-empty">
                Drop issues here
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
      @close="showCreate = false"
      @created="loadIssues"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import IssueCard from '@/components/IssueCard.vue'
import CreateIssueModal from '@/components/CreateIssueModal.vue'
import { useProjectsStore } from '@/store/projects'
import { useIssuesStore } from '@/store/issues'
import { sprintsApi } from '@/api'

const route = useRoute()
const router = useRouter()
const projectsStore = useProjectsStore()
const issuesStore = useIssuesStore()
const projectId = computed(() => Number(route.params.id))
const showCreate = ref(false)
const draggedIssue = ref(null)
const dragOver = ref(null)
const sprints = ref([])
const activeSprint = computed(() => sprints.value.find(s => s.status === 'active'))

const columns = [
  { status: 'todo',        label: 'To Do',       color: '#55556a' },
  { status: 'in_progress', label: 'In Progress',  color: 'var(--accent)' },
  { status: 'in_review',   label: 'In Review',    color: 'var(--yellow)' },
  { status: 'done',        label: 'Done',         color: 'var(--green)' },
]

const issuesByStatus = (s) => issuesStore.issues.filter(i => i.status === s)

async function loadIssues() {
  const active = activeSprint.value
  await issuesStore.fetchIssues(projectId.value, active ? { sprint_id: active.id } : {})
}

onMounted(async () => {
  await projectsStore.fetchProject(projectId.value)
  const r = await sprintsApi.list(projectId.value)
  sprints.value = r.data
  await loadIssues()
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
.sidebar {
  width: 200px; flex-shrink: 0; background: var(--bg2); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; padding: 1rem 0.75rem; gap: 2px; overflow-y: auto;
}
.sidebar-section-title {
  font-size: 0.68rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--text3); padding: 0.5rem 0.5rem 0.25rem; margin-top: 0.25rem;
}
.sidebar-item {
  display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 7px;
  font-size: 0.84rem; color: var(--text2); cursor: pointer; transition: all 0.15s; text-decoration: none;
}
.sidebar-item:hover { background: rgba(255,255,255,0.05); color: var(--text); }
.sidebar-item.active { background: rgba(92,79,255,0.15); color: var(--accent2); }
.icon { font-size: 0.9rem; width: 18px; text-align: center; }
.sprint-info { padding: 8px 10px; border-radius: 7px; background: rgba(0,217,126,0.08); border: 1px solid rgba(0,217,126,0.15); }
.sprint-badge { font-size: 0.65rem; color: var(--green); font-weight: 600; margin-bottom: 3px; }
.sprint-name { font-size: 0.8rem; color: var(--text); font-weight: 500; }
.sprint-empty { font-size: 0.78rem; color: var(--text3); padding: 6px 10px; }

/* Board */
.content { flex: 1; overflow-x: auto; padding: 1.5rem; display: flex; flex-direction: column; }
.board-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.25rem; }
.board-title { font-family: var(--font-display); font-size: 1.3rem; font-weight: 700; letter-spacing: -0.02em; }
.board-sub { font-size: 0.82rem; color: var(--text2); margin-top: 2px; }
.board-columns { display: flex; gap: 14px; flex: 1; min-width: max-content; align-items: flex-start; }
.board-col { width: 280px; flex-shrink: 0; display: flex; flex-direction: column; }
.col-header { display: flex; align-items: center; gap: 7px; margin-bottom: 10px; }
.col-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.col-name { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; color: var(--text2); }
.col-count {
  font-size: 0.65rem; color: var(--text3); background: var(--bg2);
  padding: 1px 7px; border-radius: 100px; margin-left: 2px;
}
.col-body {
  display: flex; flex-direction: column; gap: 7px; min-height: 80px;
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 10px; padding: 8px; transition: background 0.15s, border-color 0.15s;
}
.board-col.drag-over .col-body {
  background: rgba(92,79,255,0.06); border-color: rgba(92,79,255,0.4);
}
.col-empty { font-size: 0.75rem; color: var(--text3); text-align: center; padding: 12px 0; }
</style>
