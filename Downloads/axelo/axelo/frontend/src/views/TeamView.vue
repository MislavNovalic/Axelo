<template>
  <div class="team-page">
    <div class="team-header">
      <div>
        <h1 class="page-title">Team</h1>
        <p class="page-sub">{{ project?.name }} · {{ members.length }} member{{ members.length !== 1 ? 's' : '' }}</p>
      </div>
      <button v-if="canManage" class="btn-primary" @click="showInvite = true">+ Invite Member</button>
    </div>

    <!-- Members table -->
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
      <h3 class="legend-title">Role Permissions</h3>
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
import { projectsApi } from '@/api'

const route = useRoute()
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

// Invite
const showInvite = ref(false)
const inviteEmail = ref('')
const inviteRole = ref('member')
const inviteError = ref('')
const inviting = ref(false)

// Remove
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

function confirmRemove(member) {
  removeTarget.value = member
}

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
  {
    role: 'owner',
    perms: ['Full project control', 'Delete project', 'Manage all members', 'All admin permissions']
  },
  {
    role: 'admin',
    perms: ['Invite & remove members', 'Change member roles', 'Manage sprints', 'Edit any issue']
  },
  {
    role: 'member',
    perms: ['Create issues', 'Edit own issues', 'Comment on issues', 'View all content']
  },
  {
    role: 'viewer',
    perms: ['View all issues', 'View sprints', 'View board & backlog', 'Read-only access']
  }
]
</script>

<style scoped>
.team-page { padding: 2rem 2.5rem; max-width: 960px; margin: 0 auto; }

.team-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 2rem;
}
.page-title { font-size: 1.5rem; font-weight: 700; color: var(--text); margin: 0 0 4px; }
.page-sub { font-size: 0.83rem; color: var(--text3); margin: 0; }

/* Table */
.members-card {
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 12px; overflow: hidden; margin-bottom: 2rem;
}
.table-head, .table-row {
  display: grid;
  grid-template-columns: 1fr 140px 140px 48px;
  align-items: center;
  padding: 0 1.25rem;
}
.table-head {
  height: 40px;
  background: var(--bg3);
  font-size: 0.72rem; font-weight: 600; color: var(--text3);
  letter-spacing: 0.05em; text-transform: uppercase;
  border-bottom: 1px solid var(--border);
}
.table-row {
  height: 60px;
  border-bottom: 1px solid var(--border);
  transition: background 0.12s;
}
.table-row:last-child { border-bottom: none; }
.table-row:hover { background: rgba(255,255,255,0.02); }

.col-user { display: flex; align-items: center; gap: 12px; }
.member-avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: var(--accent); color: #fff;
  font-size: 0.72rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.member-name { font-size: 0.88rem; font-weight: 500; color: var(--text); }
.member-email { font-size: 0.75rem; color: var(--text3); margin-top: 1px; }

.col-joined { font-size: 0.8rem; color: var(--text3); }
.col-actions { display: flex; justify-content: flex-end; }

/* Role badge */
.role-badge {
  display: inline-block; padding: 3px 10px; border-radius: 20px;
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.02em;
}
.role-owner  { background: rgba(255,209,102,0.15); color: #ffd166; }
.role-admin  { background: rgba(92,79,255,0.15);   color: var(--accent2); }
.role-member { background: rgba(0,217,126,0.12);   color: #00d97e; }
.role-viewer { background: rgba(144,144,176,0.12); color: var(--text2); }

/* Role select — styled like badge */
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

/* Legend */
.role-legend { margin-top: 2.5rem; }
.legend-title { font-size: 0.85rem; font-weight: 600; color: var(--text2); margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.05em; }
.legend-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.legend-card {
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 10px; padding: 1rem;
}
.legend-header { margin-bottom: 0.75rem; }
.legend-perms { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.perm-item { font-size: 0.78rem; color: var(--text2); display: flex; gap: 6px; align-items: flex-start; }
.perm-check { color: var(--green); font-size: 0.7rem; flex-shrink: 0; margin-top: 1px; }

/* Modal */
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
.field-input {
  width: 100%; padding: 8px 12px; border-radius: 8px;
  border: 1px solid var(--border2); background: var(--bg3);
  color: var(--text); font-size: 0.88rem; outline: none;
  box-sizing: border-box; font-family: var(--font-body);
}
.field-input:focus { border-color: var(--accent); }
.error-msg { font-size: 0.8rem; color: var(--red); margin-top: 0.5rem; }
.confirm-text { font-size: 0.88rem; color: var(--text2); line-height: 1.5; }
.confirm-text strong { color: var(--text); }

/* Buttons */
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

@media (max-width: 700px) {
  .legend-grid { grid-template-columns: 1fr 1fr; }
  .table-head, .table-row { grid-template-columns: 1fr 110px; }
  .col-joined, .col-actions { display: none; }
}
</style>
