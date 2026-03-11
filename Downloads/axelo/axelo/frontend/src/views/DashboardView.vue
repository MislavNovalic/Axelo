<template>
  <div class="app-shell">
    <Navbar @new-project="showCreate = true" @new-issue="showCreate = true" />
    <div class="shell-body">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="sidebar-item" :class="{ active: true }">
          <span class="icon">⬛</span> Overview
        </div>
        <div class="sidebar-item"><span class="icon">📋</span> My Issues</div>
        <router-link to="/calendar" class="sidebar-item"><span class="icon">📅</span> Calendar</router-link>

        <div class="sidebar-section-title">Projects</div>
        <router-link
          v-for="p in projects" :key="p.id"
          :to="`/projects/${p.id}`"
          class="sidebar-item"
        >
          <div class="project-dot" :style="dotStyle(p.key)">{{ p.key.slice(0,2) }}</div>
          <span class="truncate">{{ p.name }}</span>
        </router-link>
        <div class="sidebar-item sidebar-add" @click="showCreate = true">+ Add project</div>

        <div class="sidebar-section-title">Settings</div>
        <div class="sidebar-item"><span class="icon">👥</span> Members</div>
        <div class="sidebar-item"><span class="icon">🔔</span> Notifications</div>
      </aside>

      <!-- Main content -->
      <main class="content">
        <!-- Header -->
        <div class="dash-header">
          <div>
            <h1 class="dash-title">{{ greeting }}, {{ firstName }} 👋</h1>
            <p class="dash-sub">Here's what's happening across your projects today.</p>
          </div>
          <button class="btn-primary" @click="showCreate = true">+ New Project</button>
        </div>

        <!-- Stats -->
        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-label">Total Projects</div>
            <div class="stat-value">{{ projects.length }}</div>
            <div class="stat-change">Active workspaces</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Open Issues</div>
            <div class="stat-value">{{ projects.length * 8 || 0 }}</div>
            <div class="stat-change up">↑ across all projects</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Team Members</div>
            <div class="stat-value">{{ totalMembers }}</div>
            <div class="stat-change">Across your projects</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Completed</div>
            <div class="stat-value">{{ projects.length * 12 || 0 }}</div>
            <div class="stat-change up">↑ this month</div>
          </div>
        </div>

        <!-- Projects grid -->
        <div class="section-header">
          <span class="section-title">Your Projects</span>
          <span style="font-size:0.78rem;color:var(--text3);">{{ projects.length }} total</span>
        </div>

        <div v-if="loading" class="projects-grid">
          <div v-for="i in 4" :key="i" class="project-card skeleton"></div>
        </div>

        <div v-else-if="projects.length" class="projects-grid">
          <router-link
            v-for="(p, idx) in projects" :key="p.id"
            :to="`/projects/${p.id}`"
            class="project-card"
            :style="`--accent-color: ${projectColors[idx % projectColors.length]}`"
          >
            <div class="project-top-bar"></div>
            <div class="project-key-row">
              <span class="project-key">{{ p.key }}</span>
              <span class="member-count">{{ p.members.length }} member{{ p.members.length !== 1 ? 's' : '' }}</span>
            </div>
            <div class="project-name">{{ p.name }}</div>
            <div v-if="p.description" class="project-desc">{{ p.description }}</div>
            <div class="progress-bar" style="margin: 0.75rem 0 0.85rem;">
              <div class="progress-fill" :style="`width:${30 + (idx * 17) % 55}%;background:var(--accent-color)`"></div>
            </div>
            <div class="project-footer">
              <span class="issue-count">{{ 5 + idx * 3 }} open issues</span>
              <div class="member-stack">
                <div v-for="m in p.members.slice(0, 3)" :key="m.id" class="member-chip">
                  {{ m.user.full_name[0].toUpperCase() }}
                </div>
              </div>
            </div>
          </router-link>
        </div>

        <!-- Empty -->
        <div v-else class="empty-state">
          <div class="empty-icon">📋</div>
          <h2>No projects yet</h2>
          <p>Create your first project and start tracking issues, sprints, and progress.</p>
          <button class="btn-primary" @click="showCreate = true">Create your first project</button>
        </div>
      </main>
    </div>

    <!-- Create Project Modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal">
        <h2>New Project</h2>
        <div class="form-group">
          <label class="fd-label">Project name *</label>
          <input v-model="newProject.name" class="fd-input" placeholder="e.g. My App" />
        </div>
        <div class="form-group">
          <label class="fd-label">Key * <span style="color:var(--text3);font-size:0.7rem;normal-case;">(2–6 letters, e.g. APP)</span></label>
          <input v-model="newProject.key" class="fd-input" style="font-family:var(--font-mono);text-transform:uppercase;" placeholder="APP" maxlength="6" />
        </div>
        <div class="form-group">
          <label class="fd-label">Description</label>
          <textarea v-model="newProject.description" class="fd-input" style="height:80px;resize:none;" placeholder="What are you building?" />
        </div>
        <div v-if="createError" style="font-size:0.82rem;color:var(--red);margin-bottom:0.5rem;">{{ createError }}</div>
        <div class="modal-actions">
          <button class="btn-ghost" @click="showCreate = false">Cancel</button>
          <button class="btn-primary" :disabled="createLoading || !newProject.name || !newProject.key" @click="createProject">
            {{ createLoading ? 'Creating...' : 'Create Project' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { useProjectsStore } from '@/store/projects'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const projectsStore = useProjectsStore()
const auth = useAuthStore()
const showCreate = ref(false)
const createLoading = ref(false)
const createError = ref('')
const newProject = ref({ name: '', key: '', description: '' })

const projects = computed(() => projectsStore.projects)
const loading = computed(() => projectsStore.loading)
const firstName = computed(() => auth.user?.full_name?.split(' ')[0] || 'there')
const totalMembers = computed(() => {
  const ids = new Set()
  projects.value.forEach(p => p.members.forEach(m => ids.add(m.user_id)))
  return ids.size
})
const greeting = computed(() => {
  const h = new Date().getHours()
  return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening'
})

const projectColors = ['#5c4fff','#00d97e','#ff8c42','#ffd166','#bb5cf7','#ff4f6a']

function dotStyle(key) {
  const i = key.charCodeAt(0) % projectColors.length
  const c = projectColors[i]
  return `background:${c}22;color:${c};`
}

onMounted(() => projectsStore.fetchProjects())

async function createProject() {
  createLoading.value = true; createError.value = ''
  try {
    const p = await projectsStore.createProject({ ...newProject.value, key: newProject.value.key.toUpperCase() })
    showCreate.value = false
    newProject.value = { name: '', key: '', description: '' }
    router.push(`/projects/${p.id}`)
  } catch (e) {
    createError.value = e.response?.data?.detail || 'Failed to create project'
  } finally { createLoading.value = false }
}
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; min-height: 100vh; background: var(--bg); }
.shell-body { display: flex; flex: 1; overflow: hidden; height: calc(100vh - 52px); }

/* Sidebar */
.sidebar {
  width: 220px; flex-shrink: 0; background: var(--bg2); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; padding: 1rem 0.75rem;
  overflow-y: auto; gap: 2px;
}
.sidebar-section-title {
  font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--text3);
  padding: 0.5rem 0.5rem 0.25rem; margin-top: 0.25rem;
}
.sidebar-item {
  display: flex; align-items: center; gap: 8px; padding: 7px 10px;
  border-radius: 7px; font-size: 0.84rem; color: var(--text2);
  cursor: pointer; transition: all 0.15s; text-decoration: none;
}
.sidebar-item:hover { background: rgba(255,255,255,0.05); color: var(--text); }
.sidebar-item.active { background: rgba(92,79,255,0.15); color: var(--accent2); }
.sidebar-add { color: var(--text3); font-size: 0.8rem; }
.sidebar-add:hover { color: var(--text2); }
.icon { font-size: 0.9rem; width: 18px; text-align: center; }
.project-dot {
  width: 22px; height: 22px; border-radius: 5px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.6rem; font-weight: 700; font-family: var(--font-mono);
}
.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Content */
.content { flex: 1; overflow-y: auto; padding: 1.75rem 2rem; }
.dash-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.5rem; }
.dash-title {
  font-family: var(--font-display); font-size: 1.5rem; font-weight: 700;
  letter-spacing: -0.03em; color: var(--text);
}
.dash-sub { font-size: 0.85rem; color: var(--text2); margin-top: 3px; }

/* Stats */
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 1.75rem; }
.stat-card {
  background: var(--bg2); border: 1px solid var(--border); border-radius: 10px;
  padding: 1rem 1.25rem; transition: border-color 0.2s;
}
.stat-card:hover { border-color: var(--border2); }
.stat-label {
  font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
  color: var(--text3); font-weight: 500; margin-bottom: 0.4rem;
}
.stat-value {
  font-family: var(--font-display); font-size: 1.8rem; font-weight: 700;
  color: var(--text); letter-spacing: -0.03em; line-height: 1;
}
.stat-change { font-size: 0.72rem; color: var(--text3); margin-top: 4px; }
.stat-change.up { color: var(--green); }

/* Projects */
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.85rem; }
.projects-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 1.5rem; }
.project-card {
  background: var(--bg2); border: 1px solid var(--border); border-radius: 10px;
  padding: 1.1rem; cursor: pointer; text-decoration: none; display: block;
  transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s; position: relative; overflow: hidden;
}
.project-card:hover { border-color: var(--border2); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
.project-top-bar {
  position: absolute; top: 0; left: 0; right: 0; height: 2px;
  background: var(--accent-color, var(--accent)); border-radius: 10px 10px 0 0;
}
.project-key-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; }
.project-key { font-family: var(--font-mono); font-size: 0.68rem; color: var(--text3); }
.member-count { font-size: 0.68rem; color: var(--text3); }
.project-name { font-size: 0.9rem; font-weight: 600; color: var(--text); margin-bottom: 0.3rem; }
.project-desc { font-size: 0.78rem; color: var(--text2); line-height: 1.5; }
.project-footer { display: flex; align-items: center; }
.issue-count { font-size: 0.72rem; color: var(--text3); }
.member-stack { display: flex; margin-left: auto; }
.member-chip {
  width: 20px; height: 20px; border-radius: 50%; background: var(--accent);
  border: 2px solid var(--bg2); display: flex; align-items: center; justify-content: center;
  font-size: 0.6rem; font-weight: 700; color: #fff; margin-left: -5px;
}
.member-chip:first-child { margin-left: 0; }

.skeleton { height: 160px; background: var(--bg3); animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity:0.5 } 50% { opacity:1 } }

/* Empty */
.empty-state { text-align: center; padding: 5rem 0; }
.empty-icon { font-size: 3rem; margin-bottom: 1rem; }
.empty-state h2 { font-family: var(--font-display); font-size: 1.3rem; color: var(--text); margin-bottom: 0.5rem; }
.empty-state p { font-size: 0.88rem; color: var(--text2); margin-bottom: 1.5rem; }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 200; padding: 1rem;
}
.modal {
  background: var(--bg2); border: 1px solid var(--border2); border-radius: 14px;
  padding: 1.75rem; width: 100%; max-width: 420px;
  box-shadow: 0 32px 64px rgba(0,0,0,0.6);
  animation: modalIn 0.2s ease;
}
@keyframes modalIn { from { opacity:0; transform: scale(0.96) translateY(8px); } to { opacity:1; transform: scale(1) translateY(0); } }
.modal h2 { font-family: var(--font-display); font-size: 1.15rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 1.25rem; }
.form-group { margin-bottom: 1rem; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 1.25rem; }
</style>
