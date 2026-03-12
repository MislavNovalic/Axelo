<template>
  <div class="app-shell">
    <Navbar />
    <div class="shell-body">
      <main v-if="issue" class="content">
        <button class="back-btn" @click="router.back()">← Back</button>

        <div class="issue-layout">
          <!-- Main col -->
          <div class="issue-main">
            <div class="issue-header-card">
              <div class="issue-meta-row">
                <span class="issue-key-tag">{{ issue.key }}</span>
                <span class="type-badge" :class="`type-${issue.type}`">{{ issue.type }}</span>
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
                <input v-model="newComment" class="fd-input" placeholder="Add a comment..." @keyup.enter="submitComment" />
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
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
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
                <input type="number" :value="issue.story_points" @change="updateField('story_points', Number($event.target.value))" class="fd-input" min="0" />
              </div>
              <div class="divider"></div>
              <div class="field-group">
                <label class="fd-label">Reporter</label>
                <div class="reporter-row">
                  <div class="reporter-avatar">{{ issue.reporter.full_name[0].toUpperCase() }}</div>
                  <span class="reporter-name">{{ issue.reporter.full_name }}</span>
                </div>
              </div>
              <div class="field-group">
                <label class="fd-label">Created</label>
                <div style="font-size:0.82rem;color:var(--text2);">{{ formatDate(issue.created_at) }}</div>
              </div>
            </div>
            <button class="delete-btn" @click="deleteIssue">Delete Issue</button>
          </div>
        </div>
      </main>

      <div v-else class="loading-state">
        <div class="loading-spinner"></div>
        <span>Loading issue...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { formatDistanceToNow } from 'date-fns'
import Navbar from '@/components/Navbar.vue'
import { useIssuesStore } from '@/store/issues'
import { useAuthStore } from '@/store/auth'
import { useWebSocket } from '@/composables/useWebSocket'

const route = useRoute()
const router = useRouter()
const issuesStore = useIssuesStore()
const authStore = useAuthStore()
const projectId = computed(() => Number(route.params.id))
const issueId = computed(() => Number(route.params.issueId))
const issue = computed(() => issuesStore.currentIssue)
const newComment = ref('')
const editingTitle = ref(false)
const editTitle = ref('')
const editingDesc = ref(false)
const editDesc = ref('')
const titleInput = ref(null)

onMounted(() => {
  issuesStore.fetchIssue(projectId.value, issueId.value)
  const token = authStore.token
  if (token) {
    useWebSocket(projectId.value, token, {
      'comment.created': (data) => {
        if (data.issue_id === issueId.value) {
          issuesStore.fetchIssue(projectId.value, issueId.value)
        }
      },
      'issue.updated': (data) => {
        if (data.id === issueId.value) {
          issuesStore.fetchIssue(projectId.value, issueId.value)
        }
      },
    })
  }
})

const formatDate = (d) => formatDistanceToNow(new Date(d), { addSuffix: true })
const updateField = (field, value) => issuesStore.updateIssue(projectId.value, issueId.value, { [field]: value })

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
.back-btn {
  display: inline-flex; align-items: center; gap: 6px; font-size: 0.82rem;
  color: var(--text3); cursor: pointer; border: none; background: none;
  padding: 0; margin-bottom: 1.25rem; transition: color 0.15s;
}
.back-btn:hover { color: var(--text2); }

.issue-layout { display: grid; grid-template-columns: 1fr 280px; gap: 1.25rem; }
.issue-main { display: flex; flex-direction: column; gap: 1rem; }

.issue-header-card {
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 10px; padding: 1.5rem;
}
.issue-meta-row { display: flex; align-items: center; gap: 8px; margin-bottom: 0.75rem; }
.issue-key-tag { font-family: var(--font-mono); font-size: 0.72rem; color: var(--text3); }
.type-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 500; }
.type-badge.type-bug { background: rgba(255,79,106,0.12); color: var(--red); }
.type-badge.type-story { background: rgba(0,217,126,0.12); color: var(--green); }
.type-badge.type-task { background: rgba(92,79,255,0.12); color: var(--accent2); }
.type-badge.type-epic { background: rgba(187,92,247,0.12); color: #bb5cf7; }
.issue-title {
  font-family: var(--font-display); font-size: 1.4rem; font-weight: 700;
  letter-spacing: -0.02em; color: var(--text); margin-bottom: 1rem; cursor: pointer; line-height: 1.3;
}
.issue-title:hover { color: var(--text2); }
.issue-title-input { font-family: var(--font-display); font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem; }
.desc-section { margin-top: 0.25rem; }
.desc-body {
  font-size: 0.88rem; color: var(--text2); line-height: 1.65; min-height: 40px;
  cursor: pointer; padding: 10px; border-radius: 6px; border: 1px solid transparent; transition: border-color 0.15s;
}
.desc-body:hover { border-color: var(--border); }

.comments-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; }
.section-header-row { display: flex; align-items: center; gap: 8px; margin-bottom: 1rem; }
.comment-count {
  font-size: 0.7rem; color: var(--text3); background: var(--bg3);
  padding: 1px 7px; border-radius: 100px;
}
.comment-list { display: flex; flex-direction: column; gap: 0; margin-bottom: 1rem; }
.comment-item { display: flex; gap: 10px; padding: 10px 0; border-bottom: 1px solid var(--border); }
.comment-item:last-child { border-bottom: none; }
.comment-avatar {
  width: 26px; height: 26px; border-radius: 50%; background: var(--accent); flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-size: 0.68rem; font-weight: 700; color: #fff; margin-top: 2px;
}
.comment-meta { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.comment-author { font-size: 0.82rem; font-weight: 500; color: var(--text); }
.comment-time { font-size: 0.72rem; color: var(--text3); }
.comment-text { font-size: 0.83rem; color: var(--text2); line-height: 1.55; }
.comment-input-row { display: flex; gap: 8px; }
.comment-input-row .fd-input { flex: 1; }

.issue-sidebar { display: flex; flex-direction: column; gap: 10px; }
.sidebar-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 1.1rem; }
.field-group { margin-bottom: 1rem; }
.field-group:last-child { margin-bottom: 0; }
.divider { height: 1px; background: var(--border); margin: 0.75rem 0; }
.reporter-row { display: flex; align-items: center; gap: 8px; }
.reporter-avatar {
  width: 22px; height: 22px; border-radius: 50%; background: var(--accent);
  display: flex; align-items: center; justify-content: center; font-size: 0.62rem; font-weight: 700; color: #fff;
}
.reporter-name { font-size: 0.83rem; color: var(--text2); }
.delete-btn {
  width: 100%; padding: 8px; border-radius: 8px; cursor: pointer; border: none;
  background: rgba(255,79,106,0.08); color: var(--red); font-size: 0.82rem;
  font-family: var(--font-body); transition: background 0.15s;
}
.delete-btn:hover { background: rgba(255,79,106,0.15); }

.loading-state { display: flex; align-items: center; justify-content: center; gap: 10px; height: 100%; color: var(--text3); font-size: 0.88rem; }
.loading-spinner {
  width: 18px; height: 18px; border-radius: 50%;
  border: 2px solid var(--border); border-top-color: var(--accent);
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
