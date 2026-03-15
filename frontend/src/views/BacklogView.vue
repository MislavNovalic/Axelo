<template>
  <div class="app-shell">
    <Navbar @new-issue="showCreate = true" />
    <div class="shell-body">
      <aside class="sidebar">
        <router-link to="/" class="sidebar-item"><span class="icon">⬛</span> Overview</router-link>
        <router-link :to="`/projects/${projectId}`" class="sidebar-item"><span class="icon">📌</span> Board</router-link>
        <div class="sidebar-item active"><span class="icon">📋</span> Backlog</div>
      </aside>

      <main class="content">
        <div class="page-header">
          <div>
            <h1 class="page-title">Backlog</h1>
            <p class="page-sub">Manage sprints and plan your work</p>
          </div>
          <div style="display:flex;gap:8px;">
            <button class="btn-ghost" @click="showCreateSprint = true">+ Sprint</button>
            <button class="btn-primary" @click="showCreate = true">+ Issue</button>
          </div>
        </div>

        <!-- Sprints -->
        <div v-for="sprint in sprints" :key="sprint.id" class="sprint-section">
          <div class="sprint-header" @click="toggleCollapse(sprint.id)">
            <span class="collapse-icon">{{ collapsed[sprint.id] ? '▶' : '▼' }}</span>
            <span class="sprint-name">{{ sprint.name }}</span>
            <span class="sprint-status-badge" :class="`status-${sprint.status}`">{{ sprint.status }}</span>
            <span class="sprint-meta">{{ sprint.issues.length }} issues</span>
            <div class="sprint-actions">
              <button v-if="sprint.status === 'planned'" class="action-btn" @click.stop="startSprint(sprint)">Start Sprint</button>
              <button v-if="sprint.status === 'active'" class="action-btn green" @click.stop="completeSprint(sprint)">Complete</button>
            </div>
          </div>

          <div v-if="!collapsed[sprint.id]" class="issue-list">
            <div v-for="issue in sprint.issues" :key="issue.id" class="issue-row" @click="openIssue(issue)">
              <div class="issue-row-dot" :class="`dot-${issue.status}`"></div>
              <span class="issue-row-key">{{ issue.key }}</span>
              <span class="issue-row-title">{{ issue.title }}</span>
              <span class="issue-row-badge" :class="`priority-${issue.priority}`">{{ issue.priority }}</span>
              <span class="issue-row-badge" :class="`status-text-${issue.status}`">{{ issue.status.replace('_',' ') }}</span>
            </div>
            <div v-if="!sprint.issues.length" class="issue-list-empty">No issues in this sprint yet</div>
          </div>
        </div>

        <!-- Backlog -->
        <div class="sprint-section">
          <div class="sprint-header" @click="toggleCollapse('backlog')">
            <span class="collapse-icon">{{ collapsed['backlog'] ? '▶' : '▼' }}</span>
            <span class="sprint-name">Backlog</span>
            <span class="sprint-meta">{{ backlogIssues.length }} issues</span>
          </div>
          <div v-if="!collapsed['backlog']" class="issue-list">
            <div v-for="issue in backlogIssues" :key="issue.id" class="issue-row" @click="openIssue(issue)">
              <div class="issue-row-dot dot-backlog"></div>
              <span class="issue-row-key">{{ issue.key }}</span>
              <span class="issue-row-title">{{ issue.title }}</span>
              <span class="issue-row-badge" :class="`priority-${issue.priority}`">{{ issue.priority }}</span>
            </div>
            <div v-if="!backlogIssues.length" class="issue-list-empty">No unplanned issues</div>
          </div>
        </div>
      </main>
    </div>

    <CreateIssueModal v-if="showCreate" :project-id="projectId" :sprints="sprints" @close="showCreate = false" @created="loadData" />

    <!-- Create Sprint Modal -->
    <div v-if="showCreateSprint" class="modal-overlay" @click.self="showCreateSprint = false">
      <div class="modal">
        <h2>New Sprint</h2>
        <div class="form-group">
          <label class="fd-label">Sprint name *</label>
          <input v-model="sprintForm.name" class="fd-input" placeholder="e.g. Sprint 1" />
        </div>
        <div class="form-group">
          <label class="fd-label">Goal <span style="color:var(--text3)">(optional)</span></label>
          <input v-model="sprintForm.goal" class="fd-input" placeholder="What will be achieved?" />
        </div>
        <div class="modal-actions">
          <button class="btn-ghost" @click="showCreateSprint = false">Cancel</button>
          <button class="btn-primary" :disabled="!sprintForm.name" @click="createSprint">Create Sprint</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import CreateIssueModal from '@/components/CreateIssueModal.vue'
import { useProjectsStore } from '@/store/projects'
import { useIssuesStore } from '@/store/issues'
import { sprintsApi } from '@/api'

const route = useRoute()
const router = useRouter()
const projectsStore = useProjectsStore()
const issuesStore = useIssuesStore()
const projectId = computed(() => Number(route.params.id))
const sprints = ref([])
const showCreate = ref(false)
const showCreateSprint = ref(false)
const collapsed = reactive({})
const sprintForm = ref({ name: '', goal: '' })

const backlogIssues = computed(() => issuesStore.issues.filter(i => !i.sprint_id && i.status === 'backlog'))

onMounted(loadData)

async function loadData() {
  await projectsStore.fetchProject(projectId.value)
  const [sr] = await Promise.all([sprintsApi.list(projectId.value), issuesStore.fetchIssues(projectId.value)])
  sprints.value = sr.data
}

function toggleCollapse(id) { collapsed[id] = !collapsed[id] }
function openIssue(issue) { router.push(`/projects/${projectId.value}/issues/${issue.id}`) }

async function createSprint() {
  await sprintsApi.create(projectId.value, sprintForm.value)
  sprintForm.value = { name: '', goal: '' }
  showCreateSprint.value = false
  await loadData()
}
async function startSprint(s) { await sprintsApi.update(projectId.value, s.id, { status: 'active' }); await loadData() }
async function completeSprint(s) { await sprintsApi.update(projectId.value, s.id, { status: 'completed' }); await loadData() }
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; min-height: 100vh; background: var(--bg); }
.shell-body { display: flex; flex: 1; height: calc(100vh - 52px); overflow: hidden; }
.sidebar {
  width: 200px; flex-shrink: 0; background: var(--bg2); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; padding: 1rem 0.75rem; gap: 2px;
}
.sidebar-item {
  display: flex; align-items: center; gap: 8px; padding: 7px 10px; border-radius: 7px;
  font-size: 0.84rem; color: var(--text2); cursor: pointer; transition: all 0.15s; text-decoration: none;
}
.sidebar-item:hover { background: rgba(255,255,255,0.05); color: var(--text); }
.sidebar-item.active { background: rgba(16,185,129,0.15); color: var(--accent2); }
.icon { font-size: 0.9rem; width: 18px; text-align: center; }
.content { flex: 1; overflow-y: auto; padding: 1.75rem 2rem; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.5rem; }
.page-title { font-family: var(--font-display); font-size: 1.3rem; font-weight: 700; letter-spacing: -0.02em; }
.page-sub { font-size: 0.82rem; color: var(--text2); margin-top: 2px; }

.sprint-section { margin-bottom: 1rem; background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.sprint-header {
  display: flex; align-items: center; gap: 10px; padding: 12px 16px;
  cursor: pointer; transition: background 0.15s;
}
.sprint-header:hover { background: rgba(255,255,255,0.03); }
.collapse-icon { font-size: 0.65rem; color: var(--text3); width: 12px; }
.sprint-name { font-size: 0.9rem; font-weight: 600; color: var(--text); }
.sprint-status-badge {
  font-size: 0.65rem; padding: 2px 8px; border-radius: 100px; font-weight: 500;
}
.status-planned { background: rgba(255,255,255,0.06); color: var(--text3); }
.status-active { background: rgba(0,217,126,0.12); color: var(--green); border: 1px solid rgba(0,217,126,0.2); }
.status-completed { background: rgba(16,185,129,0.12); color: var(--accent2); }
.sprint-meta { font-size: 0.75rem; color: var(--text3); }
.sprint-actions { margin-left: auto; display: flex; gap: 6px; }
.action-btn {
  font-size: 0.72rem; padding: 3px 10px; border-radius: 5px; cursor: pointer; border: none;
  background: rgba(16,185,129,0.15); color: var(--accent2); font-weight: 500;
  transition: background 0.15s;
}
.action-btn:hover { background: rgba(16,185,129,0.25); }
.action-btn.green { background: rgba(0,217,126,0.12); color: var(--green); }
.action-btn.green:hover { background: rgba(0,217,126,0.22); }

.issue-list { border-top: 1px solid var(--border); }
.issue-row {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 16px; cursor: pointer; transition: background 0.12s;
  border-bottom: 1px solid var(--border);
}
.issue-row:last-child { border-bottom: none; }
.issue-row:hover { background: rgba(255,255,255,0.03); }
.issue-row-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.dot-backlog { background: var(--text3); }
.dot-todo { background: var(--text2); }
.dot-in_progress { background: var(--accent); }
.dot-in_review { background: var(--yellow); }
.dot-done { background: var(--green); }
.issue-row-key { font-family: var(--font-mono); font-size: 0.68rem; color: var(--text3); width: 64px; flex-shrink: 0; }
.issue-row-title { font-size: 0.82rem; color: var(--text2); flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.issue-row-badge { font-size: 0.65rem; padding: 2px 7px; border-radius: 4px; flex-shrink: 0; font-weight: 500; }
.priority-critical { background: rgba(255,79,106,0.1); color: var(--red); }
.priority-high { background: rgba(255,140,66,0.1); color: var(--orange); }
.priority-medium { background: rgba(255,209,102,0.1); color: var(--yellow); }
.priority-low { background: rgba(100,180,255,0.1); color: #64b4ff; }
.issue-list-empty { padding: 12px 16px; font-size: 0.78rem; color: var(--text3); font-style: italic; }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 200; padding: 1rem;
}
.modal {
  background: var(--bg2); border: 1px solid var(--border2); border-radius: 14px;
  padding: 1.75rem; width: 100%; max-width: 400px; box-shadow: 0 32px 64px rgba(0,0,0,0.6);
  animation: modalIn 0.2s ease;
}
@keyframes modalIn { from { opacity:0; transform:scale(0.96); } to { opacity:1; transform:scale(1); } }
.modal h2 { font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 1.25rem; }
.form-group { margin-bottom: 1rem; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 1.25rem; }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .sidebar { display: none; }
}
@media (max-width: 640px) {
  .content { padding: 1rem 0.75rem; }
  .page-header { flex-direction: column; align-items: flex-start; gap: 8px; }
  .sprint-header { flex-wrap: wrap; }
}
</style>
