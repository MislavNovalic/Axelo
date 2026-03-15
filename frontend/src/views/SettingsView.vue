<template>
  <div class="app-shell">
    <Navbar />
    <div class="settings-page">
      <div class="settings-header">
        <h1 class="page-title">Settings</h1>
        <p class="page-sub">Manage your team, integrations, and account security</p>
      </div>

      <!-- Team Members -->
      <div class="section">
        <div class="section-header">
          <div>
            <h3 class="section-title">👥 Team Members</h3>
            <p class="section-sub">{{ project?.name }} · {{ members.length }} member{{ members.length !== 1 ? 's' : '' }}</p>
          </div>
          <button v-if="canManage" class="btn-primary btn-sm" @click="showInvite = true">+ Invite Member</button>
        </div>
        <div class="members-card">
          <div class="members-table">
            <div class="table-head">
              <div class="col-user">Member</div>
              <div class="col-role">Role</div>
              <div class="col-joined">Joined</div>
              <div v-if="canManage" class="col-actions"></div>
            </div>
            <div v-for="m in members" :key="m.id" class="table-row">
              <div class="col-user">
                <div class="member-avatar">{{ initials(m.user.full_name) }}</div>
                <div class="member-info">
                  <div class="member-name">{{ m.user.full_name }}</div>
                  <div class="member-email">{{ m.user.email }}</div>
                </div>
              </div>
              <div class="col-role">
                <select
                  v-if="canManage && m.role !== 'owner' && m.user.id !== currentUser?.id"
                  class="role-select"
                  :value="m.role"
                  :class="['role-badge', `role-${m.role}`]"
                  @change="changeRole(m.user.id, $event.target.value)"
                >
                  <option value="admin">Admin</option>
                  <option value="member">Member</option>
                  <option value="viewer">Viewer</option>
                </select>
                <span v-else :class="['role-badge', `role-${m.role}`]">{{ roleLabel(m.role) }}</span>
              </div>
              <div class="col-joined">{{ formatDate(m.joined_at) }}</div>
              <div v-if="canManage" class="col-actions">
                <button
                  v-if="m.role !== 'owner' && m.user.id !== currentUser?.id"
                  class="btn-remove"
                  @click="confirmRemove(m)"
                  title="Remove member"
                >✕</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Role legend -->
        <div class="role-legend">
          <div class="legend-title">Role Permissions</div>
          <div class="legend-grid">
            <div v-for="r in roleInfo" :key="r.role" class="legend-card">
              <div class="legend-header">
                <span :class="['role-badge', `role-${r.role}`]">{{ roleLabel(r.role) }}</span>
              </div>
              <ul class="legend-perms">
                <li v-for="p in r.perms" :key="p" class="perm-item">
                  <span class="perm-check">✓</span> {{ p }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Issue Templates -->
      <div class="section">
        <div class="section-header">
          <h3 class="section-title">📋 Issue Templates</h3>
          <button class="btn-sm btn-ghost" @click="showTemplateForm = !showTemplateForm">+ New Template</button>
        </div>
        <div v-if="showTemplateForm" class="template-form">
          <div class="gh-row">
            <input v-model="tplForm.name" class="field-input" placeholder="Template name (e.g. Bug Report)" />
            <select v-model="tplForm.type" class="field-input">
              <option value="bug">Bug</option><option value="task">Task</option>
              <option value="story">Story</option><option value="epic">Epic</option>
            </select>
            <select v-model="tplForm.priority" class="field-input">
              <option value="critical">Critical</option><option value="high">High</option>
              <option value="medium">Medium</option><option value="low">Low</option>
            </select>
          </div>
          <input v-model="tplForm.title_template" class="field-input" placeholder="Title template (e.g. [Bug] <description>)" />
          <textarea v-model="tplForm.body_template" class="field-input tpl-body" placeholder="Body template (Markdown supported)…" rows="4"></textarea>
          <div class="tpl-footer">
            <button class="btn-ghost btn-sm" @click="showTemplateForm = false">Cancel</button>
            <button class="btn-primary btn-sm" @click="createTemplate" :disabled="!tplForm.name">Save Template</button>
          </div>
        </div>
        <div v-if="templates.length" class="template-list">
          <div v-for="t in templates" :key="t.id" class="tpl-row">
            <span class="tpl-dot" :class="`type-${t.type}`"></span>
            <span class="tpl-name">{{ t.name }}</span>
            <span class="tpl-type">{{ t.type }}</span>
            <button class="icon-btn" @click="deleteTemplate(t.id)" title="Delete">🗑</button>
          </div>
        </div>
        <p v-else-if="!showTemplateForm" class="empty-hint">No templates yet. Create one to speed up issue creation.</p>
      </div>

      <!-- Outbound Webhooks -->
      <div v-if="canManage" class="section">
        <div class="section-header">
          <div>
            <h3 class="section-title">🔗 Outbound Webhooks</h3>
            <p class="section-sub">Send real-time events to Slack, Zapier, n8n, or any custom endpoint.</p>
          </div>
        </div>
        <WebhooksPanel :project-id="projectId" />
      </div>

      <!-- GitHub Integration -->
      <div class="section">
        <div class="section-header">
          <h3 class="section-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>
            GitHub Integration
          </h3>
        </div>
        <div v-if="githubInfo" class="github-connected">
          <div class="github-repo">
            <span class="repo-icon">📦</span>
            <a :href="`https://github.com/${githubInfo.repo}`" target="_blank" class="repo-link">{{ githubInfo.repo }}</a>
            <span class="connected-badge">Connected</span>
          </div>
          <p class="github-hint">Commits and PRs referencing issue keys (e.g. <code>fixes AX-42</code>) will link automatically.</p>
          <div class="webhook-box">
            <span class="wh-label">Webhook URL:</span>
            <code class="wh-url">/api/integrations/github/webhook?project_id={{ projectId }}</code>
          </div>
          <div v-if="githubInfo.recent_links?.length" class="recent-links">
            <div class="rl-title">Recent Links</div>
            <div v-for="l in githubInfo.recent_links" :key="l.id" class="rl-row">
              <span class="rl-type" :class="l.link_type">{{ l.link_type === 'pr' ? '⤴ PR' : '⬤ commit' }}</span>
              <a :href="l.gh_url" target="_blank" class="rl-title-link">{{ l.gh_title }}</a>
              <span class="rl-state" :class="l.gh_state">{{ l.gh_state }}</span>
            </div>
          </div>
          <button class="btn-danger btn-sm" @click="disconnectGitHub">Disconnect</button>
        </div>
        <div v-else class="github-connect-form">
          <p class="form-hint">Connect a GitHub repo to link PRs and commits to issues.</p>
          <div class="gh-row">
            <input v-model="ghForm.repo_owner" class="field-input" placeholder="owner (e.g. MislavNovalic)" />
            <input v-model="ghForm.repo_name" class="field-input" placeholder="repo (e.g. axelo)" />
          </div>
          <div class="gh-row">
            <input v-model="ghForm.webhook_secret" class="field-input" placeholder="Webhook secret (optional)" type="password" />
          </div>
          <button class="btn-primary btn-sm" @click="connectGitHub" :disabled="!ghForm.repo_owner || !ghForm.repo_name">
            Connect Repository
          </button>
        </div>
      </div>

      <!-- Security / 2FA -->
      <div class="section">
        <div class="section-header">
          <h3 class="section-title">🔐 Security</h3>
          <p class="section-sub">Two-factor authentication for your account.</p>
        </div>
        <TwoFactorSettings />
      </div>
    </div>

    <!-- Invite Modal -->
    <div v-if="showInvite" class="modal-backdrop" @click.self="showInvite = false">
      <div class="modal">
        <div class="modal-header">
          <h2 class="modal-title">Invite Member</h2>
          <button class="modal-close" @click="showInvite = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="field">
            <label class="field-label">Email address</label>
            <input v-model="inviteEmail" class="field-input" type="email" placeholder="user@example.com" @keyup.enter="sendInvite" />
          </div>
          <div class="field">
            <label class="field-label">Role</label>
            <select v-model="inviteRole" class="field-input">
              <option value="admin">Admin — can manage members and issues</option>
              <option value="member" selected>Member — can create and edit issues</option>
              <option value="viewer">Viewer — read only</option>
            </select>
          </div>
          <p v-if="inviteError" class="error-msg">{{ inviteError }}</p>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="showInvite = false">Cancel</button>
          <button class="btn-primary" :disabled="inviting" @click="sendInvite">
            {{ inviting ? 'Inviting…' : 'Send Invite' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Remove confirm -->
    <div v-if="removeTarget" class="modal-backdrop" @click.self="removeTarget = null">
      <div class="modal modal-sm">
        <div class="modal-header">
          <h2 class="modal-title">Remove Member</h2>
          <button class="modal-close" @click="removeTarget = null">✕</button>
        </div>
        <div class="modal-body">
          <p class="confirm-text">Remove <strong>{{ removeTarget.user.full_name }}</strong> from this project? They will lose access immediately.</p>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="removeTarget = null">Cancel</button>
          <button class="btn-danger" :disabled="removing" @click="doRemove">
            {{ removing ? 'Removing…' : 'Remove' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectsStore } from '@/store/projects'
import { useAuthStore } from '@/store/auth'
import { githubApi, projectsApi, templatesApi } from '@/api'
import Navbar from '@/components/Navbar.vue'
import TwoFactorSettings from '@/components/TwoFactorSettings.vue'
import WebhooksPanel from '@/components/WebhooksPanel.vue'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const projectsStore = useProjectsStore()
const authStore = useAuthStore()

const project = computed(() => projectsStore.currentProject)
const currentUser = computed(() => authStore.user)
const members = computed(() => project.value?.members || [])

const canManage = computed(() => {
  if (!project.value || !currentUser.value) return false
  const me = members.value.find(m => m.user.id === currentUser.value.id)
  return me && (me.role === 'owner' || me.role === 'admin')
})

// GitHub
const githubInfo = ref(null)
const ghForm = ref({ repo_owner: '', repo_name: '', webhook_secret: '' })

async function loadGitHub() {
  try { const r = await githubApi.get(projectId.value); githubInfo.value = r.data } catch { }
}
async function connectGitHub() {
  await githubApi.connect(projectId.value, ghForm.value)
  await loadGitHub()
  ghForm.value = { repo_owner: '', repo_name: '', webhook_secret: '' }
}
async function disconnectGitHub() {
  if (!confirm('Disconnect GitHub integration?')) return
  await githubApi.disconnect(projectId.value)
  githubInfo.value = null
}

// Team
const showInvite = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('member')
const inviteError = ref('')
const inviting = ref(false)
const removeTarget = ref(null)
const removing = ref(false)

function initials(name) {
  return name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || '?'
}
function roleLabel(role) {
  return { owner: 'Owner', admin: 'Admin', member: 'Member', viewer: 'Viewer' }[role] || role
}
function formatDate(dt) {
  if (!dt) return '—'
  return new Date(dt).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

async function changeRole(userId, newRole) {
  try {
    const updated = await projectsApi.updateMemberRole(project.value.id, userId, { role: newRole })
    projectsStore.currentProject = updated.data
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to update role')
  }
}
function confirmRemove(member) { removeTarget.value = member }
async function doRemove() {
  if (!removeTarget.value) return
  removing.value = true
  try {
    const updated = await projectsApi.removeMember(project.value.id, removeTarget.value.user.id)
    projectsStore.currentProject = updated.data
    removeTarget.value = null
  } catch (e) {
    alert(e.response?.data?.detail || 'Failed to remove member')
  } finally {
    removing.value = false
  }
}
async function sendInvite() {
  inviteError.value = ''
  if (!inviteEmail.value.trim()) { inviteError.value = 'Email is required'; return }
  inviting.value = true
  try {
    const updated = await projectsApi.addMember(project.value.id, { email: inviteEmail.value.trim(), role: inviteRole.value })
    projectsStore.currentProject = updated.data
    showInvite.value = false
    inviteEmail.value = ''
    inviteRole.value = 'member'
  } catch (e) {
    inviteError.value = e.response?.data?.detail || 'Failed to invite member'
  } finally {
    inviting.value = false
  }
}

const roleInfo = [
  { role: 'owner', perms: ['Full project control', 'Delete project', 'Manage all members', 'All admin permissions'] },
  { role: 'admin', perms: ['Invite & remove members', 'Change member roles', 'Manage sprints', 'Edit any issue'] },
  { role: 'member', perms: ['Create issues', 'Edit own issues', 'Comment on issues', 'View all content'] },
  { role: 'viewer', perms: ['View all issues', 'View sprints', 'View board & backlog', 'Read-only access'] }
]

// Templates
const templates = ref([])
const showTemplateForm = ref(false)
const tplForm = ref({ name: '', type: 'bug', priority: 'medium', title_template: '', body_template: '' })

async function loadTemplates() {
  try { const r = await templatesApi.list(projectId.value); templates.value = r.data } catch { }
}
async function createTemplate() {
  await templatesApi.create(projectId.value, tplForm.value)
  await loadTemplates()
  showTemplateForm.value = false
  tplForm.value = { name: '', type: 'bug', priority: 'medium', title_template: '', body_template: '' }
}
async function deleteTemplate(id) {
  if (!confirm('Delete this template?')) return
  await templatesApi.delete(projectId.value, id)
  templates.value = templates.value.filter(t => t.id !== id)
}

onMounted(async () => {
  if (!projectsStore.currentProject || projectsStore.currentProject.id !== projectId.value) {
    await projectsStore.fetchProject(projectId.value)
  }
  await Promise.all([loadGitHub(), loadTemplates()])
})
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; min-height: 100vh; background: var(--bg); }
.settings-page { padding: 2rem 2.5rem; max-width: 960px; margin: 0 auto; width: 100%; box-sizing: border-box; }

.settings-header { margin-bottom: 2rem; }
.page-title { font-size: 1.5rem; font-weight: 700; color: var(--text); margin: 0 0 4px; }
.page-sub { font-size: 0.83rem; color: var(--text3); margin: 0; }

.section {
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;
}
.section-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 1rem; gap: 8px;
}
.section-title {
  font-size: 0.95rem; font-weight: 600; color: var(--text);
  margin: 0; display: flex; align-items: center; gap: 8px;
}
.section-sub { font-size: 0.8rem; color: var(--text3); margin: 2px 0 0; }

/* Members table */
.members-card {
  border: 1px solid var(--border); border-radius: 10px; overflow: hidden; margin-bottom: 1.5rem;
}
.table-head, .table-row {
  display: grid;
  grid-template-columns: 1fr 140px 140px 48px;
  align-items: center;
  padding: 0 1rem;
}
.table-head {
  height: 38px;
  background: var(--bg3);
  font-size: 0.72rem; font-weight: 600; color: var(--text3);
  letter-spacing: 0.05em; text-transform: uppercase;
  border-bottom: 1px solid var(--border);
}
.table-row {
  height: 58px;
  border-bottom: 1px solid var(--border);
  transition: background 0.12s;
}
.table-row:last-child { border-bottom: none; }
.table-row:hover { background: rgba(255,255,255,0.02); }
.col-user { display: flex; align-items: center; gap: 10px; }
.member-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: var(--accent); color: #fff;
  font-size: 0.72rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.member-name { font-size: 0.88rem; font-weight: 500; color: var(--text); }
.member-email { font-size: 0.75rem; color: var(--text3); margin-top: 1px; }
.col-joined { font-size: 0.8rem; color: var(--text3); }
.col-actions { display: flex; justify-content: flex-end; }

.role-badge {
  display: inline-block; padding: 3px 10px; border-radius: 20px;
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.02em;
}
.role-owner  { background: rgba(255,209,102,0.15); color: #ffd166; }
.role-admin  { background: rgba(16,185,129,0.15);   color: var(--accent2); }
.role-member { background: rgba(0,217,126,0.12);   color: #00d97e; }
.role-viewer { background: rgba(144,144,176,0.12); color: var(--text2); }

.role-select {
  border: none; cursor: pointer; outline: none;
  padding: 3px 10px; border-radius: 20px;
  font-size: 0.75rem; font-weight: 600;
  appearance: none; -webkit-appearance: none;
}
.role-select:focus { outline: 2px solid var(--accent); }

.btn-remove {
  width: 28px; height: 28px; border-radius: 6px;
  border: 1px solid var(--border); background: transparent;
  color: var(--text3); cursor: pointer; font-size: 11px;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.btn-remove:hover { border-color: var(--red); color: var(--red); background: rgba(255,79,106,0.08); }

/* Role legend */
.role-legend { margin-top: 0.5rem; }
.legend-title { font-size: 0.72rem; color: var(--text3); margin-bottom: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
.legend-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; }
.legend-card {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: 10px; padding: 0.85rem;
}
.legend-header { margin-bottom: 0.6rem; }
.legend-perms { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 5px; }
.perm-item { font-size: 0.76rem; color: var(--text2); display: flex; gap: 6px; align-items: flex-start; }
.perm-check { color: var(--green); font-size: 0.7rem; flex-shrink: 0; margin-top: 1px; }

/* Templates */
.template-form { background: var(--bg3); border-radius: 10px; padding: 1rem; margin-bottom: 1rem; display: flex; flex-direction: column; gap: 0.6rem; }
.tpl-body { resize: vertical; min-height: 80px; }
.tpl-footer { display: flex; gap: 8px; justify-content: flex-end; }
.template-list { display: flex; flex-direction: column; gap: 4px; }
.tpl-row { display: flex; align-items: center; gap: 8px; padding: 8px 10px; background: var(--bg3); border-radius: 8px; }
.tpl-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.type-bug   { background: var(--red); }
.type-story { background: var(--green); }
.type-task  { background: var(--accent2); }
.type-epic  { background: #06b6d4; }
.tpl-name { flex: 1; font-size: 0.82rem; font-weight: 500; color: var(--text); }
.tpl-type { font-size: 0.68rem; color: var(--text3); background: var(--bg2); padding: 2px 6px; border-radius: 4px; }
.icon-btn { background: none; border: none; cursor: pointer; font-size: 0.85rem; opacity: 0.4; transition: opacity 0.15s; }
.icon-btn:hover { opacity: 1; }
.empty-hint { font-size: 0.78rem; color: var(--text3); padding: 0.25rem 0; }

/* GitHub */
.github-connected { display: flex; flex-direction: column; gap: 0.75rem; }
.github-repo { display: flex; align-items: center; gap: 8px; }
.repo-icon { font-size: 1rem; }
.repo-link { color: var(--accent2); text-decoration: none; font-weight: 600; }
.repo-link:hover { text-decoration: underline; }
.connected-badge { background: rgba(0,217,126,0.12); color: var(--green); font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 8px; }
.github-hint { font-size: 0.78rem; color: var(--text2); }
.github-hint code { background: var(--bg3); padding: 1px 5px; border-radius: 4px; font-family: var(--font-mono); font-size: 0.75rem; }
.webhook-box { background: var(--bg3); padding: 8px 12px; border-radius: 8px; display: flex; align-items: center; gap: 8px; }
.wh-label { font-size: 0.72rem; color: var(--text3); flex-shrink: 0; }
.wh-url { font-family: var(--font-mono); font-size: 0.7rem; color: var(--text2); }
.recent-links { margin-top: 0.5rem; }
.rl-title { font-size: 0.72rem; color: var(--text3); margin-bottom: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
.rl-row { display: flex; align-items: center; gap: 8px; padding: 4px 0; border-bottom: 1px solid var(--border); }
.rl-type { font-size: 0.68rem; font-weight: 700; font-family: var(--font-mono); min-width: 60px; }
.rl-type.pr { color: var(--accent2); }
.rl-type.commit { color: var(--text3); }
.rl-title-link { flex: 1; font-size: 0.78rem; color: var(--text); text-decoration: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rl-title-link:hover { color: var(--accent2); }
.rl-state { font-size: 0.65rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; text-transform: capitalize; }
.rl-state.open   { background: rgba(0,217,126,0.12); color: var(--green); }
.rl-state.merged { background: rgba(16,185,129,0.12); color: var(--accent2); }
.rl-state.closed { background: rgba(255,79,106,0.12); color: var(--red); }
.rl-state.committed { background: rgba(144,144,176,0.1); color: var(--text3); }
.github-connect-form { display: flex; flex-direction: column; gap: 0.6rem; }
.form-hint { font-size: 0.78rem; color: var(--text2); }
.gh-row { display: flex; gap: 8px; }
.gh-row .field-input { flex: 1; }

/* Modals */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(0,0,0,0.55);
  display: flex; align-items: center; justify-content: center; z-index: 500;
}
.modal {
  background: var(--bg2); border: 1px solid var(--border2);
  border-radius: 14px; padding: 0; width: 440px;
  box-shadow: 0 24px 60px rgba(0,0,0,0.5);
}
.modal-sm { width: 360px; }
.modal-header {
  padding: 1.25rem 1.5rem 1rem;
  display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--border);
}
.modal-title { font-size: 1rem; font-weight: 600; color: var(--text); margin: 0; }
.modal-close { background: none; border: none; color: var(--text3); cursor: pointer; font-size: 1rem; line-height: 1; }
.modal-body { padding: 1.25rem 1.5rem; }
.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--border);
  display: flex; justify-content: flex-end; gap: 8px;
}
.field { margin-bottom: 1rem; }
.field:last-child { margin-bottom: 0; }
.field-label { display: block; font-size: 0.78rem; font-weight: 600; color: var(--text2); margin-bottom: 6px; }
.confirm-text { font-size: 0.88rem; color: var(--text2); line-height: 1.5; }
.confirm-text strong { color: var(--text); }
.error-msg { font-size: 0.8rem; color: var(--red); margin-top: 0.5rem; }

/* Shared inputs & buttons */
.field-input {
  width: 100%; padding: 8px 12px; border-radius: 8px;
  border: 1px solid var(--border2); background: var(--bg3);
  color: var(--text); font-size: 0.88rem; outline: none;
  box-sizing: border-box; font-family: var(--font-body);
}
.field-input:focus { border-color: var(--accent); }

.btn-sm { padding: 5px 12px; font-size: 0.78rem; font-weight: 600; border-radius: 6px; cursor: pointer; font-family: var(--font-body); transition: all 0.15s; }
.btn-primary {
  padding: 8px 16px; border-radius: 8px;
  background: var(--accent); color: #fff;
  border: none; cursor: pointer; font-size: 0.83rem; font-weight: 600;
  font-family: var(--font-body); transition: opacity 0.15s;
}
.btn-primary:hover { opacity: 0.88; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-ghost {
  padding: 8px 16px; border-radius: 8px;
  background: transparent; color: var(--text2);
  border: 1px solid var(--border2); cursor: pointer;
  font-size: 0.83rem; font-family: var(--font-body); transition: all 0.15s;
}
.btn-ghost:hover { color: var(--text); border-color: var(--text3); }
.btn-danger {
  padding: 8px 16px; border-radius: 8px;
  background: rgba(255,79,106,0.15); color: var(--red);
  border: 1px solid rgba(255,79,106,0.3); cursor: pointer;
  font-size: 0.83rem; font-family: var(--font-body); transition: all 0.15s;
}
.btn-danger:hover { background: rgba(255,79,106,0.25); }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 1024px) {
  .legend-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 700px) {
  .table-head, .table-row { grid-template-columns: 1fr 110px; }
  .col-joined, .col-actions { display: none; }
}
@media (max-width: 640px) {
  .settings-page { padding: 1rem; }
  .gh-row { flex-direction: column; }
  .legend-grid { grid-template-columns: 1fr 1fr; }
  .modal { width: calc(100vw - 2rem); }
}
</style>
