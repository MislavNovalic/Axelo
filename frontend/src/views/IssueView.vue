<template>
  <div class="app-shell">
    <Navbar />
    <div class="shell-body">
      <main v-if="issue" class="content">
        <!-- Real-time update banner -->
        <Transition name="rt-banner">
          <div v-if="remoteUpdateBanner" class="rt-banner">
            <span>🔄</span> A teammate just updated this issue
          </div>
        </Transition>
        <div class="breadcrumb">
          <button class="back-btn" @click="router.back()">← Back</button>
          <span class="bc-sep">·</span>
          <span class="bc-key">{{ issue.key }}</span>
        </div>

        <div class="issue-layout">
          <!-- Main col -->
          <div class="issue-main">
            <div class="issue-header-card">
              <div class="issue-meta-row">
                <span :class="['type-badge', `type-${issue.type}`]">{{ issue.type }}</span>
                <span :class="['priority-badge', `priority-${issue.priority}`]">{{ priorityIcon(issue.priority) }} {{ issue.priority }}</span>
                <span :class="['status-badge', `status-${issue.status}`]">{{ statusLabel(issue.status) }}</span>
              </div>

              <h1 v-if="!editingTitle" class="issue-title" @dblclick="startEditTitle">{{ issue.title }}</h1>
              <input
                v-else v-model="editTitle" class="fd-input issue-title-input"
                ref="titleInput" @blur="saveTitle" @keyup.enter="saveTitle" @keyup.escape="editingTitle = false"
              />

              <div class="desc-section">
                <div class="fd-label" style="margin-bottom:0.5rem;">Description</div>
                <div v-if="!editingDesc" class="desc-body" @dblclick="startEditDesc">
                  {{ issue.description || 'Double-click to add a description...' }}
                </div>
                <div v-else>
                  <textarea v-model="editDesc" class="fd-input" style="height:120px;resize:none;" />
                  <div style="display:flex;gap:8px;margin-top:8px;">
                    <button class="btn-primary" style="padding:5px 14px;font-size:0.8rem;" @click="saveDesc">Save</button>
                    <button class="btn-ghost" style="padding:5px 14px;font-size:0.8rem;" @click="editingDesc = false">Cancel</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Comments -->
            <div class="comments-card">
              <div class="section-header-row">
                <span class="section-title">Comments</span>
                <span class="comment-count">{{ issue.comments.length }}</span>
              </div>
              <div v-if="!issue.comments.length" class="no-comments">No comments yet. Be the first to leave one.</div>
              <div class="comment-list">
                <div v-for="c in issue.comments" :key="c.id" class="comment-item">
                  <div class="comment-avatar">{{ c.author.full_name[0].toUpperCase() }}</div>
                  <div class="comment-body">
                    <div class="comment-meta">
                      <span class="comment-author">{{ c.author.full_name }}</span>
                      <span class="comment-time">{{ formatDate(c.created_at) }}</span>
                    </div>
                    <p class="comment-text">{{ c.body }}</p>
                  </div>
                </div>
              </div>
              <div class="comment-input-row">
                <div class="self-avatar">{{ selfInitial }}</div>
                <input v-model="newComment" class="fd-input" placeholder="Leave a comment..." @keyup.enter="submitComment" />
                <button class="btn-primary" :disabled="!newComment.trim()" @click="submitComment">Post</button>
              </div>
            </div>
          </div>

          <!-- Sidebar -->
          <div class="issue-sidebar">
            <div class="sidebar-card">
              <div class="field-group">
                <label class="fd-label">Status</label>
                <select :value="issue.status" @change="updateField('status', $event.target.value)" class="fd-input">
                  <option value="backlog">Backlog</option>
                  <option value="todo">To Do</option>
                  <option value="in_progress">In Progress</option>
                  <option value="in_review">In Review</option>
                  <option value="done">Done</option>
                </select>
              </div>
              <div class="field-group">
                <label class="fd-label">Priority</label>
                <select :value="issue.priority" @change="updateField('priority', $event.target.value)" class="fd-input">
                  <option value="low">🟢 Low</option>
                  <option value="medium">🟡 Medium</option>
                  <option value="high">🟠 High</option>
                  <option value="critical">🔴 Critical</option>
                </select>
              </div>
              <div class="field-group">
                <label class="fd-label">Type</label>
                <select :value="issue.type" @change="updateField('type', $event.target.value)" class="fd-input">
                  <option value="task">Task</option>
                  <option value="bug">Bug</option>
                  <option value="story">Story</option>
                  <option value="epic">Epic</option>
                </select>
              </div>
              <div class="field-group">
                <label class="fd-label">Story Points</label>
                <input type="number" :value="issue.story_points" @change="updateField('story_points', Number($event.target.value))" class="fd-input" min="0" placeholder="—" />
              </div>
              <div class="field-group">
                <label class="fd-label">Assignee</label>
                <select :value="issue.assignee?.id ?? ''" @change="updateField('assignee_id', $event.target.value ? Number($event.target.value) : null)" class="fd-input">
                  <option value="">Unassigned</option>
                  <option v-for="m in projectMembers" :key="m.user.id" :value="m.user.id">{{ m.user.full_name }}</option>
                </select>
                <div v-if="issue.assignee" class="assignee-chip">
                  <div class="assignee-avatar">{{ issue.assignee.full_name[0].toUpperCase() }}</div>
                  <span class="assignee-name">{{ issue.assignee.full_name }}</span>
                </div>
                <div v-else class="assignee-chip unassigned">
                  <div class="assignee-avatar" style="background:var(--bg3);color:var(--text3)">?</div>
                  <span class="assignee-name" style="color:var(--text3)">Unassigned</span>
                </div>
              </div>
              <div class="divider"></div>
              <div class="field-group">
                <label class="fd-label">Reporter</label>
                <div class="assignee-chip">
                  <div class="assignee-avatar">{{ issue.reporter.full_name[0].toUpperCase() }}</div>
                  <span class="assignee-name">{{ issue.reporter.full_name }}</span>
                </div>
              </div>
              <div class="field-group">
                <label class="fd-label">Created</label>
                <div style="font-size:0.82rem;color:var(--text2);">{{ formatDate(issue.created_at) }}</div>
              </div>
            </div>
            <button class="delete-btn" @click="deleteIssue">🗑 Delete Issue</button>
          </div>
        </div>

        <!-- File attachments -->
        <FileAttachments
          v-if="issue"
          :project-id="projectId"
          :issue-id="issueId"
        />

        <!-- Custom Fields -->
        <CustomFieldsPanel
          v-if="issue"
          :project-id="projectId"
          :issue-id="issueId"
        />

        <!-- Time Tracking -->
        <TimeTrackingPanel
          v-if="issue"
          :project-id="projectId"
          :issue-id="issueId"
          :can-write="canWrite"
          :is-admin="isAdmin"
        />

        <!-- AI Summary — Phase 4 -->
        <AiIssueSummary
          v-if="issue"
          :project-id="projectId"
          :issue-id="issueId"
        />
      </main>

      <div v-else class="loading-state">
        <div class="loading-spinner"></div>
        <span>Loading issue...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { formatDistanceToNow } from 'date-fns'
import Navbar from '@/components/Navbar.vue'
import FileAttachments from '@/components/FileAttachments.vue'
import CustomFieldsPanel from '@/components/CustomFieldsPanel.vue'
import TimeTrackingPanel from '@/components/TimeTrackingPanel.vue'
import AiIssueSummary from '@/components/AiIssueSummary.vue'
import { useIssuesStore } from '@/store/issues'
import { useProjectsStore } from '@/store/projects'
import { useAuthStore } from '@/store/auth'
import { useWsStore } from '@/store/ws'

const route = useRoute()
const router = useRouter()
const issuesStore = useIssuesStore()
const projectsStore = useProjectsStore()
const authStore = useAuthStore()
const wsStore = useWsStore()
const projectId = computed(() => Number(route.params.id))
const issueId = computed(() => Number(route.params.issueId))
const issue = computed(() => issuesStore.currentIssue)
const newComment = ref('')
const editingTitle = ref(false); const editTitle = ref('')
const editingDesc = ref(false); const editDesc = ref('')
const titleInput = ref(null)
const remoteUpdateBanner = ref(false)

const projectMembers = computed(() => projectsStore.currentProject?.members || [])
const currentMember = computed(() => projectMembers.value.find(m => m.user_id === authStore.user?.id))
const canWrite = computed(() => currentMember.value && currentMember.value.role !== 'viewer')
const isAdmin = computed(() => currentMember.value && ['admin', 'owner'].includes(currentMember.value.role))
const selfInitial = computed(() => authStore.user?.full_name?.[0]?.toUpperCase() || '?')

// ── Real-time handlers ──────────────────────────────────────────────────────
function onIssueUpdated(data) {
  if (data.id !== issueId.value) return
  // Patch currentIssue in place
  if (issuesStore.currentIssue) {
    Object.assign(issuesStore.currentIssue, data)
    remoteUpdateBanner.value = true
    setTimeout(() => { remoteUpdateBanner.value = false }, 3000)
  }
}
function onCommentAdded(data) {
  if (data.issue_id !== issueId.value) return
  const issue = issuesStore.currentIssue
  if (!issue) return
  if (!issue.comments) issue.comments = []
  if (!issue.comments.find(c => c.id === data.id)) {
    issue.comments.push({
      id: data.id,
      body: data.body,
      created_at: data.created_at,
      author: { id: data.author_id, full_name: data.author_name }
    })
  }
}

onMounted(async () => {
  await issuesStore.fetchIssue(projectId.value, issueId.value)
  if (!projectsStore.currentProject || projectsStore.currentProject.id !== projectId.value) {
    await projectsStore.fetchProject(projectId.value)
  }
  wsStore.connect(projectId.value)
  wsStore.on('issue_updated',  onIssueUpdated)
  wsStore.on('comment_added',  onCommentAdded)
})

onBeforeUnmount(() => {
  wsStore.off('issue_updated', onIssueUpdated)
  wsStore.off('comment_added', onCommentAdded)
  wsStore.connect(null)
})

const formatDate = (d) => formatDistanceToNow(new Date(d), { addSuffix: true })
const updateField = (field, value) => issuesStore.updateIssue(projectId.value, issueId.value, { [field]: value })

function statusLabel(s) { return { backlog:'Backlog', todo:'To Do', in_progress:'In Progress', in_review:'In Review', done:'Done' }[s] || s }
function priorityIcon(p) { return { low:'🟢', medium:'🟡', high:'🟠', critical:'🔴' }[p] || '' }

function startEditTitle() { editTitle.value = issue.value.title; editingTitle.value = true; nextTick(() => titleInput.value?.focus()) }
async function saveTitle() { if (editTitle.value.trim()) await updateField('title', editTitle.value.trim()); editingTitle.value = false }
function startEditDesc() { editDesc.value = issue.value.description || ''; editingDesc.value = true }
async function saveDesc() { await updateField('description', editDesc.value); editingDesc.value = false }
async function submitComment() {
  if (!newComment.value.trim()) return
  await issuesStore.addComment(projectId.value, issueId.value, newComment.value)
  newComment.value = ''
}
async function deleteIssue() {
  if (!confirm('Delete this issue?')) return
  await issuesStore.deleteIssue(projectId.value, issueId.value)
  router.back()
}
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; min-height: 100vh; background: var(--bg); }
.shell-body { flex: 1; overflow: hidden; height: calc(100vh - 52px); }
.content { height: 100%; overflow-y: auto; padding: 1.5rem 2rem; max-width: 1100px; margin: 0 auto; }

.breadcrumb { display: flex; align-items: center; gap: 8px; margin-bottom: 1.25rem; }
.back-btn { display: inline-flex; align-items: center; font-size: 0.82rem; color: var(--text3); cursor: pointer; border: none; background: none; padding: 0; transition: color 0.15s; }
.back-btn:hover { color: var(--text2); }
.bc-sep { color: var(--text3); font-size: 0.8rem; }
.bc-key { font-family: var(--font-mono); font-size: 0.78rem; color: var(--text2); }

.issue-layout { display: grid; grid-template-columns: 1fr 280px; gap: 1.25rem; }
.issue-main { display: flex; flex-direction: column; gap: 1rem; }

.issue-header-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 1.5rem; }
.issue-meta-row { display: flex; align-items: center; gap: 6px; margin-bottom: 0.9rem; flex-wrap: wrap; }

.type-badge { padding: 3px 9px; border-radius: 5px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
.type-bug   { background: rgba(255,79,106,0.12); color: var(--red); }
.type-story { background: rgba(0,217,126,0.12); color: var(--green); }
.type-task  { background: rgba(16,185,129,0.12); color: var(--accent2); }
.type-epic  { background: rgba(187,92,247,0.12); color: #06b6d4; }

.priority-badge { padding: 3px 9px; border-radius: 5px; font-size: 0.7rem; font-weight: 500; text-transform: capitalize; background: var(--bg3); color: var(--text2); }
.priority-critical { color: var(--red); background: rgba(255,79,106,0.1); }
.priority-high     { color: var(--orange); background: rgba(255,140,66,0.1); }

.status-badge { padding: 3px 9px; border-radius: 5px; font-size: 0.7rem; font-weight: 600; }
.status-todo        { background: rgba(144,144,176,0.15); color: var(--text2); }
.status-in_progress { background: rgba(16,185,129,0.15); color: var(--accent2); }
.status-in_review   { background: rgba(255,209,102,0.15); color: #ffd166; }
.status-done        { background: rgba(0,217,126,0.15); color: var(--green); }
.status-backlog     { background: var(--bg3); color: var(--text3); }

.issue-title { font-family: var(--font-display); font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em; color: var(--text); margin-bottom: 1rem; cursor: pointer; line-height: 1.3; }
.issue-title:hover { color: var(--text2); }
.issue-title-input { font-family: var(--font-display); font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem; }
.desc-section { margin-top: 0.25rem; }
.desc-body { font-size: 0.88rem; color: var(--text2); line-height: 1.65; min-height: 40px; cursor: pointer; padding: 10px; border-radius: 6px; border: 1px solid transparent; transition: border-color 0.15s; }
.desc-body:hover { border-color: var(--border); }

/* Comments */
.comments-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; }
.section-header-row { display: flex; align-items: center; gap: 8px; margin-bottom: 1rem; }
.section-title { font-size: 0.88rem; font-weight: 600; color: var(--text); }
.comment-count { font-size: 0.7rem; color: var(--text3); background: var(--bg3); padding: 1px 7px; border-radius: 100px; }
.no-comments { font-size: 0.82rem; color: var(--text3); padding: 8px 0 16px; text-align: center; }
.comment-list { display: flex; flex-direction: column; margin-bottom: 1rem; }
.comment-item { display: flex; gap: 10px; padding: 10px 0; border-bottom: 1px solid var(--border); }
.comment-item:last-child { border-bottom: none; }
.comment-avatar { width: 28px; height: 28px; border-radius: 50%; background: var(--accent); flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; color: #fff; margin-top: 2px; }
.comment-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.comment-author { font-size: 0.82rem; font-weight: 500; color: var(--text); }
.comment-time { font-size: 0.72rem; color: var(--text3); }
.comment-text { font-size: 0.83rem; color: var(--text2); line-height: 1.55; }
.comment-input-row { display: flex; gap: 8px; align-items: center; }
.self-avatar { width: 28px; height: 28px; border-radius: 50%; background: var(--accent); flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; color: #fff; }
.comment-input-row .fd-input { flex: 1; }

/* Sidebar */
.issue-sidebar { display: flex; flex-direction: column; gap: 10px; }
.sidebar-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 1.1rem; }
.field-group { margin-bottom: 1rem; }
.field-group:last-child { margin-bottom: 0; }
.divider { height: 1px; background: var(--border); margin: 0.75rem 0; }
.assignee-chip { display: flex; align-items: center; gap: 8px; margin-top: 6px; }
.assignee-avatar { width: 24px; height: 24px; border-radius: 50%; background: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700; color: #fff; flex-shrink: 0; }
.assignee-name { font-size: 0.83rem; color: var(--text2); }
.delete-btn { width: 100%; padding: 9px; border-radius: 8px; cursor: pointer; border: 1px solid rgba(255,79,106,0.2); background: rgba(255,79,106,0.06); color: var(--red); font-size: 0.82rem; font-family: var(--font-body); transition: all 0.15s; }
.delete-btn:hover { background: rgba(255,79,106,0.14); border-color: rgba(255,79,106,0.4); }

.loading-state { display: flex; align-items: center; justify-content: center; gap: 10px; height: 100%; color: var(--text3); font-size: 0.88rem; }
.loading-spinner { width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--border); border-top-color: var(--accent); animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.btn-primary { padding: 8px 14px; border-radius: 7px; background: var(--accent); color: #fff; border: none; cursor: pointer; font-size: 0.82rem; font-weight: 600; font-family: var(--font-body); transition: opacity 0.15s; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-ghost { padding: 8px 14px; border-radius: 7px; background: transparent; color: var(--text2); border: 1px solid var(--border2); cursor: pointer; font-size: 0.82rem; font-family: var(--font-body); }

/* ── Real-time banner ───────────────────────────────────────────────────── */
.rt-banner {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px; margin-bottom: 1rem;
  background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3);
  border-radius: 8px; font-size: 0.82rem; color: var(--accent2); font-weight: 500;
}
.rt-banner-enter-active { animation: bannerIn 0.3s ease; }
.rt-banner-leave-active { animation: bannerIn 0.2s ease reverse; }
@keyframes bannerIn {
  from { opacity: 0; transform: translateY(-6px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .issue-layout { grid-template-columns: 1fr; }
  .issue-sidebar { border-left: none; border-top: 1px solid var(--border); padding-top: 1.5rem; }
}
@media (max-width: 640px) {
  .content { padding: 1rem; }
  .issue-meta-row { flex-wrap: wrap; }
  .comment-input-row { flex-wrap: wrap; }
  .comment-input-row .fd-input { min-width: 0; }
}
</style>