<template>
  <div class="orgs-page">
    <div class="page-header">
      <h1 class="page-title">Organisations</h1>
      <button class="btn-primary" @click="showCreate = true">+ New Organisation</button>
    </div>

    <!-- My orgs list -->
    <div v-if="orgs.length" class="org-grid">
      <div v-for="org in orgs" :key="org.id" class="org-card" @click="openOrg(org)">
        <div class="org-avatar" :style="{ background: orgColor(org.slug) }">
          <img v-if="org.logo_url" :src="org.logo_url" class="org-logo-img" />
          <span v-else>{{ org.name[0].toUpperCase() }}</span>
        </div>
        <div class="org-info">
          <div class="org-name">{{ org.name }}</div>
          <div class="org-slug">{{ org.slug }}</div>
          <div class="org-stats">
            <span>{{ org.member_count }} member{{ org.member_count !== 1 ? 's' : '' }}</span>
            <span class="dot-sep">·</span>
            <span>{{ org.project_count }} project{{ org.project_count !== 1 ? 's' : '' }}</span>
          </div>
        </div>
        <span class="plan-badge" :class="org.plan">{{ org.plan }}</span>
      </div>
    </div>
    <div v-else class="empty-state">
      <div class="empty-icon">🏢</div>
      <p>No organisations yet. Create one to group your projects and team.</p>
      <button class="btn-primary" @click="showCreate = true">Create your first organisation</button>
    </div>

    <!-- Org detail modal -->
    <div v-if="activeOrg" class="modal-backdrop" @click.self="activeOrg = null">
      <div class="modal modal-lg">
        <div class="modal-header">
          <div class="modal-title-row">
            <div class="org-avatar sm" :style="{ background: orgColor(activeOrg.slug) }">
              <span>{{ activeOrg.name[0].toUpperCase() }}</span>
            </div>
            <div>
              <h3>{{ activeOrg.name }}</h3>
              <div class="org-slug">{{ activeOrg.slug }}</div>
            </div>
          </div>
          <button class="btn-close" @click="activeOrg = null">✕</button>
        </div>

        <div class="modal-tabs">
          <button v-for="tab in tabs" :key="tab" class="tab-btn" :class="{ active: activeTab === tab }" @click="activeTab = tab">
            {{ tab }}
          </button>
        </div>

        <div class="modal-body">
          <!-- Members tab -->
          <div v-if="activeTab === 'Members'">
            <div class="invite-row">
              <input v-model="inviteEmail" type="email" class="field-input" placeholder="teammate@email.com" />
              <select v-model="inviteRole" class="field-input sm-input">
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
              <button class="btn-primary" @click="inviteMember" :disabled="!inviteEmail || inviting">
                {{ inviting ? '…' : 'Invite' }}
              </button>
            </div>
            <div v-if="members.length" class="member-list">
              <div v-for="m in members" :key="m.user_id" class="member-row">
                <div class="member-avatar">{{ m.full_name[0] }}</div>
                <div class="member-info">
                  <div class="member-name">{{ m.full_name }}</div>
                  <div class="member-email">{{ m.email }}</div>
                </div>
                <span class="role-badge" :class="m.role">{{ m.role }}</span>
                <button v-if="m.user_id !== activeOrg.owner_id" class="btn-del" @click="removeMember(m.user_id)">✕</button>
              </div>
            </div>
          </div>

          <!-- Projects tab -->
          <div v-if="activeTab === 'Projects'">
            <div class="attach-row">
              <select v-model="attachProjectId" class="field-input">
                <option value="" disabled>Select a project to attach…</option>
                <option v-for="p in myProjects" :key="p.id" :value="p.id">{{ p.name }} ({{ p.key }})</option>
              </select>
              <button class="btn-primary" @click="attachProject" :disabled="!attachProjectId">Attach</button>
            </div>
            <div v-if="orgProjects.length" class="project-list">
              <div v-for="p in orgProjects" :key="p.id" class="project-row">
                <span class="project-key">{{ p.key }}</span>
                <span class="project-name">{{ p.name }}</span>
                <button class="btn-ghost" @click="detachProject(p.id)">Detach</button>
              </div>
            </div>
            <div v-else class="empty-hint">No projects attached yet.</div>
          </div>

          <!-- Settings tab -->
          <div v-if="activeTab === 'Settings'">
            <div class="settings-form">
              <div class="field-group">
                <label class="field-label">Organisation name</label>
                <input v-model="editName" class="field-input" />
              </div>
              <div class="field-group">
                <label class="field-label">Logo URL (optional)</label>
                <input v-model="editLogo" class="field-input" placeholder="https://…" />
              </div>
              <div class="action-row">
                <button class="btn-primary" @click="saveSettings">Save</button>
                <button class="btn-danger-outline" @click="deleteOrg">Delete Organisation</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create org modal -->
    <div v-if="showCreate" class="modal-backdrop" @click.self="showCreate = false">
      <div class="modal">
        <div class="modal-header">
          <h3>New Organisation</h3>
          <button class="btn-close" @click="showCreate = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="field-group">
            <label class="field-label">Name</label>
            <input v-model="newName" class="field-input" placeholder="Acme Corp" @input="autoSlug" />
          </div>
          <div class="field-group">
            <label class="field-label">Slug (URL identifier)</label>
            <div class="slug-preview">axelo.app/orgs/<strong>{{ newSlug || 'your-slug' }}</strong></div>
            <input v-model="newSlug" class="field-input" placeholder="acme-corp" />
          </div>
          <div v-if="createError" class="err-msg">{{ createError }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="showCreate = false">Cancel</button>
          <button class="btn-primary" @click="createOrg" :disabled="!newName || !newSlug || creating">
            {{ creating ? 'Creating…' : 'Create' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import api from '@/api'
import { projectsApi } from '@/api'

const orgs = ref([])
const showCreate = ref(false)
const activeOrg = ref(null)
const activeTab = ref('Members')
const tabs = ['Members', 'Projects', 'Settings']

const members = ref([])
const orgProjects = ref([])
const myProjects = ref([])

const inviteEmail = ref('')
const inviteRole = ref('member')
const inviting = ref(false)
const attachProjectId = ref('')

const newName = ref('')
const newSlug = ref('')
const createError = ref('')
const creating = ref(false)

const editName = ref('')
const editLogo = ref('')

const COLORS = ['#10b981','#06b6d4','#00d97e','#ff8c42','#0095ff','#ffd166']
function orgColor(slug) {
  return COLORS[slug.charCodeAt(0) % COLORS.length]
}

function autoSlug() {
  newSlug.value = newName.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}

async function fetchOrgs() {
  const res = await api.get('/orgs/')
  orgs.value = res.data
}

async function openOrg(org) {
  activeOrg.value = org
  activeTab.value = 'Members'
  editName.value = org.name
  editLogo.value = org.logo_url || ''
  await Promise.all([fetchMembers(org), fetchOrgProjects(org)])
  myProjects.value = (await projectsApi.list()).data
}

async function fetchMembers(org) {
  const res = await api.get(`/orgs/${org.slug}/members`)
  members.value = res.data
}

async function fetchOrgProjects(org) {
  const res = await api.get(`/orgs/${org.slug}/projects`)
  orgProjects.value = res.data
}

async function createOrg() {
  creating.value = true; createError.value = ''
  try {
    await api.post('/orgs/', { name: newName.value, slug: newSlug.value })
    showCreate.value = false; newName.value = ''; newSlug.value = ''
    await fetchOrgs()
  } catch (e) {
    createError.value = e.response?.data?.detail || 'Failed to create'
  } finally { creating.value = false }
}

async function inviteMember() {
  inviting.value = true
  try {
    await api.post(`/orgs/${activeOrg.value.slug}/members`, { email: inviteEmail.value, role: inviteRole.value })
    inviteEmail.value = ''
    await fetchMembers(activeOrg.value)
  } catch (e) { alert(e.response?.data?.detail || 'Failed to invite') }
  finally { inviting.value = false }
}

async function removeMember(userId) {
  if (!confirm('Remove this member?')) return
  await api.delete(`/orgs/${activeOrg.value.slug}/members/${userId}`)
  await fetchMembers(activeOrg.value)
}

async function attachProject() {
  if (!attachProjectId.value) return
  await api.post(`/orgs/${activeOrg.value.slug}/projects/${attachProjectId.value}`)
  attachProjectId.value = ''
  await fetchOrgProjects(activeOrg.value)
}

async function detachProject(pid) {
  await api.delete(`/orgs/${activeOrg.value.slug}/projects/${pid}`)
  await fetchOrgProjects(activeOrg.value)
}

async function saveSettings() {
  await api.patch(`/orgs/${activeOrg.value.slug}`, { name: editName.value, logo_url: editLogo.value || null })
  await fetchOrgs()
  activeOrg.value = orgs.value.find(o => o.slug === activeOrg.value.slug) || activeOrg.value
}

async function deleteOrg() {
  if (!confirm(`Delete "${activeOrg.value.name}"? This cannot be undone.`)) return
  await api.delete(`/orgs/${activeOrg.value.slug}`)
  activeOrg.value = null
  await fetchOrgs()
}

onMounted(fetchOrgs)
</script>

<style scoped>
.orgs-page { padding: 2rem; max-width: 960px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.5rem; }
.page-title { font-family: var(--font-display); font-size: 1.6rem; font-weight: 800; color: var(--text); margin: 0; }
.org-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.org-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 14px; padding: 1.25rem; cursor: pointer; display: flex; align-items: center; gap: 12px; transition: border-color 0.2s, transform 0.15s; }
.org-card:hover { border-color: var(--accent); transform: translateY(-2px); }
.org-avatar { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-family: var(--font-display); font-size: 1.2rem; font-weight: 800; color: #fff; flex-shrink: 0; overflow: hidden; }
.org-avatar.sm { width: 36px; height: 36px; font-size: 1rem; border-radius: 8px; }
.org-logo-img { width: 100%; height: 100%; object-fit: cover; }
.org-info { flex: 1; min-width: 0; }
.org-name { font-size: 0.95rem; font-weight: 700; color: var(--text); }
.org-slug { font-family: var(--font-mono); font-size: 0.72rem; color: var(--text3); }
.org-stats { font-size: 0.75rem; color: var(--text3); margin-top: 3px; }
.dot-sep { margin: 0 4px; }
.plan-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; }
.plan-badge.free { background: var(--bg3); color: var(--text3); }
.plan-badge.pro { background: rgba(16,185,129,0.12); color: var(--accent2); }
.plan-badge.enterprise { background: rgba(6,182,212,0.12); color: #06b6d4; }
.empty-state { text-align: center; padding: 3rem; }
.empty-icon { font-size: 2.5rem; margin-bottom: 1rem; }
.empty-state p { color: var(--text2); font-size: 0.9rem; margin-bottom: 1rem; }
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.55); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 1rem; }
.modal { background: var(--bg2); border: 1px solid var(--border); border-radius: 18px; width: 100%; max-width: 480px; }
.modal-lg { max-width: 640px; }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border); }
.modal-title-row { display: flex; align-items: center; gap: 10px; }
.modal-header h3 { font-size: 1rem; font-weight: 700; color: var(--text); margin: 0; }
.modal-tabs { display: flex; gap: 2px; padding: 0.5rem 1.5rem; border-bottom: 1px solid var(--border); }
.tab-btn { padding: 6px 14px; background: none; border: none; border-radius: 8px; font-size: 0.83rem; color: var(--text3); cursor: pointer; transition: background 0.15s, color 0.15s; }
.tab-btn.active { background: rgba(16,185,129,0.1); color: var(--accent2); font-weight: 700; }
.modal-body { padding: 1.25rem 1.5rem; max-height: 60vh; overflow-y: auto; }
.modal-footer { padding: 1rem 1.5rem; border-top: 1px solid var(--border); display: flex; gap: 8px; justify-content: flex-end; }
.btn-close { background: none; border: none; color: var(--text3); cursor: pointer; font-size: 1rem; }
.invite-row, .attach-row { display: flex; gap: 8px; margin-bottom: 1rem; align-items: center; }
.field-input { flex: 1; padding: 9px 12px; border: 1.5px solid var(--border2); border-radius: 8px; background: var(--bg); color: var(--text); font-size: 0.85rem; outline: none; }
.field-input:focus { border-color: var(--accent); }
.sm-input { flex: 0 0 100px; }
.member-list, .project-list { display: flex; flex-direction: column; gap: 4px; }
.member-row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }
.member-avatar { width: 30px; height: 30px; border-radius: 50%; background: var(--accent); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; flex-shrink: 0; }
.member-info { flex: 1; }
.member-name { font-size: 0.85rem; font-weight: 600; color: var(--text); }
.member-email { font-size: 0.75rem; color: var(--text3); }
.role-badge { padding: 2px 7px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; text-transform: capitalize; }
.role-badge.owner { background: rgba(255,209,30,0.12); color: var(--yellow); }
.role-badge.admin { background: rgba(16,185,129,0.1); color: var(--accent2); }
.role-badge.member { background: var(--bg3); color: var(--text3); }
.btn-del { background: none; border: none; color: var(--text3); cursor: pointer; font-size: 0.8rem; }
.btn-del:hover { color: var(--red); }
.project-row { display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--border); }
.project-key { font-family: var(--font-mono); font-size: 0.78rem; color: var(--text3); flex-shrink: 0; }
.project-name { flex: 1; font-size: 0.85rem; color: var(--text); }
.empty-hint { color: var(--text3); font-size: 0.83rem; padding: 1rem 0; }
.field-group { margin-bottom: 1rem; }
.field-label { display: block; font-size: 0.75rem; font-weight: 600; color: var(--text2); margin-bottom: 5px; }
.slug-preview { font-size: 0.75rem; color: var(--text3); margin-bottom: 4px; font-family: var(--font-mono); }
.action-row { display: flex; gap: 10px; margin-top: 1rem; }
.btn-primary { padding: 9px 18px; background: var(--accent); color: #fff; border: none; border-radius: 8px; font-size: 0.85rem; font-weight: 700; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-ghost { padding: 7px 14px; background: none; border: 1px solid var(--border2); border-radius: 8px; color: var(--text2); font-size: 0.83rem; cursor: pointer; }
.btn-danger-outline { padding: 7px 14px; background: transparent; border: 1px solid rgba(255,79,106,0.4); border-radius: 8px; color: var(--red); font-size: 0.82rem; cursor: pointer; margin-left: auto; }
.err-msg { background: rgba(255,79,106,0.1); border: 1px solid rgba(255,79,106,0.3); border-radius: 8px; padding: 8px 12px; font-size: 0.82rem; color: var(--red); margin-top: 0.5rem; }
</style>
