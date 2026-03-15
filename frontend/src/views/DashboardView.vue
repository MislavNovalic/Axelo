<template>
  <div class="app-shell">
    <Navbar @new-project="showCreate = true" @new-issue="showCreate = true" />
    <div class="shell-body">

      <!-- Sidebar slides in from left -->
      <aside class="sidebar sidebar-animate">
        <router-link to="/" class="sidebar-item active"><span class="icon">⬛</span> Overview</router-link>
        <div class="sidebar-item">
          <span class="icon">📋</span> My Issues
          <span v-if="stats.my_open_issues" class="badge">{{ stats.my_open_issues }}</span>
        </div>
        <router-link to="/calendar" class="sidebar-item"><span class="icon">📅</span> Calendar</router-link>

        <div class="sidebar-section-title">Projects</div>
        <router-link v-for="p in projects" :key="p.id" :to="`/projects/${p.id}`" class="sidebar-item">
          <div class="project-dot" :style="dotStyle(p.key)">{{ p.key.slice(0,2) }}</div>
          <span class="truncate">{{ p.name }}</span>
        </router-link>
        <div class="sidebar-item sidebar-add" @click="showCreate = true">+ Add project</div>

        <div class="sidebar-section-title">Settings</div>
        <div class="sidebar-item"><span class="icon">🔔</span> Notifications</div>
      </aside>

      <main class="content">

        <!-- Header fades down -->
        <div class="dash-header anim-fade-down">
          <div>
            <h1 class="dash-title">{{ greeting }}, {{ firstName }} 👋</h1>
            <p class="dash-sub">Here's what's happening across your projects today.</p>
          </div>
          <button class="btn-primary" @click="showCreate = true">+ New Project</button>
        </div>

        <!-- Stat cards stagger in -->
        <div class="stats-row">
          <div v-for="(card, i) in statCards" :key="card.label"
               class="stat-card anim-slide-up"
               :style="`--delay:${0.05 + i * 0.08}s; --accent-color:${card.color}`">
            <div class="stat-label">{{ card.label }}</div>
            <div class="stat-value">
              <span v-if="statsLoading" class="stat-skeleton"></span>
              <AnimatedNumber v-else :target="card.value" />
            </div>
            <div class="stat-change" :class="{ up: card.up }">{{ card.sub }}</div>
            <div class="stat-bar">
              <div class="stat-bar-fill anim-bar"
                   :style="`background:${card.color}33; --bar-width:${card.barPct}%`"></div>
            </div>
          </div>
        </div>

        <!-- Projects + Activity grid -->
        <div class="main-grid">
          <div class="projects-col">
            <div class="section-header anim-fade-in" style="--delay:0.3s">
              <span class="section-title">Your Projects</span>
              <span style="font-size:0.78rem;color:var(--text3);">{{ projects.length }} total</span>
            </div>

            <div v-if="loading" class="projects-list">
              <div v-for="i in 3" :key="i" class="project-card skeleton" style="height:120px"></div>
            </div>

            <div v-else-if="projects.length" class="projects-list">
              <router-link
                v-for="(p, idx) in projects" :key="p.id"
                :to="`/projects/${p.id}`"
                class="project-card anim-slide-up"
                :style="`--delay:${0.35 + idx * 0.07}s; --accent-color:${projectColors[idx % projectColors.length]}`"
              >
                <div class="project-top-bar"></div>
                <div class="project-key-row">
                  <span class="project-key">{{ p.key }}</span>
                  <span class="member-count">{{ p.members.length }} member{{ p.members.length !== 1 ? 's' : '' }}</span>
                </div>
                <div class="project-name">{{ p.name }}</div>
                <div v-if="p.description" class="project-desc">{{ p.description }}</div>
                <div class="progress-wrap">
                  <div class="progress-bar">
                    <div class="progress-fill anim-bar"
                         :style="`--bar-width:${progressPct(idx)}%; background:var(--accent-color); --delay:${0.5 + idx * 0.07}s`"></div>
                  </div>
                  <span class="progress-label">{{ progressPct(idx) }}%</span>
                </div>
                <div class="project-footer">
                  <span class="role-chip" :class="`role-${myRole(p)}`">{{ myRole(p) }}</span>
                  <div class="member-stack">
                    <div v-for="m in p.members.slice(0, 4)" :key="m.id" class="member-chip" :title="m.user.full_name">
                      {{ m.user.full_name[0].toUpperCase() }}
                    </div>
                    <div v-if="p.members.length > 4" class="member-chip member-more">+{{ p.members.length - 4 }}</div>
                  </div>
                </div>
              </router-link>
            </div>

            <div v-else class="empty-state anim-fade-in" style="--delay:0.4s">
              <div class="empty-icon">📋</div>
              <h2>No projects yet</h2>
              <p>Create your first project and start tracking issues, sprints, and progress.</p>
              <button class="btn-primary" @click="showCreate = true">Create your first project</button>
            </div>
          </div>

          <!-- Activity feed -->
          <div class="activity-col anim-fade-in" style="--delay:0.4s">
            <div class="section-header">
              <span class="section-title">Recent Activity</span>
            </div>
            <div class="activity-list">
              <div v-if="statsLoading" v-for="i in 7" :key="i"
                   class="activity-item skeleton anim-slide-up"
                   :style="`height:52px; --delay:${0.4 + i * 0.05}s`"></div>

              <router-link
                v-else
                v-for="(issue, i) in stats.recent_issues" :key="issue.id"
                :to="`/projects/${issue.project_id}/issues/${issue.id}`"
                class="activity-item anim-slide-up"
                :style="`--delay:${0.4 + i * 0.05}s`"
              >
                <div class="activity-type-dot" :class="`type-${issue.type}`"></div>
                <div class="activity-body">
                  <div class="activity-key">{{ issue.key }}</div>
                  <div class="activity-title">{{ issue.title }}</div>
                </div>
                <div class="activity-right">
                  <span class="status-pill" :class="`status-${issue.status}`">{{ statusLabel(issue.status) }}</span>
                </div>
              </router-link>
            </div>
          </div>
        </div>

        <!-- ── Phase 4 Feature Strip ───────────────────────────────────── -->
        <div class="p4-strip anim-fade-in" style="--delay:0.6s">
          <div class="p4-strip-title">✦ Phase 4 · AI &amp; Team Features</div>
          <div class="p4-cards">
            <router-link
              v-if="projects.length"
              :to="`/projects/${projects[0].id}/ai/sprint-planner`"
              class="p4-card p4-ai"
            >
              <div class="p4-icon">✦</div>
              <div class="p4-label">AI Sprint Planner</div>
              <div class="p4-desc">Let Claude recommend your next sprint composition</div>
            </router-link>
            <router-link to="/orgs" class="p4-card p4-org">
              <div class="p4-icon">🏢</div>
              <div class="p4-label">Organisations</div>
              <div class="p4-desc">Group projects &amp; manage multi-team workspaces</div>
            </router-link>
            <router-link
              v-if="projects.length && ['owner', 'admin'].includes(myRole(projects[0]))"
              :to="`/projects/${projects[0].id}/import`"
              class="p4-card p4-import"
            >
              <div class="p4-icon">⬆</div>
              <div class="p4-label">Import Issues</div>
              <div class="p4-desc">Migrate from Jira, Linear, or CSV in one click</div>
            </router-link>
          </div>
        </div>

      </main>
    </div>

    <!-- Create Project Modal -->
    <transition name="modal-pop">
      <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
        <div class="modal">
          <h2>New Project</h2>
          <div class="form-group">
            <label class="fd-label">Project name *</label>
            <input v-model="newProject.name" class="fd-input" placeholder="e.g. My App" />
          </div>
          <div class="form-group">
            <label class="fd-label">Key * <span style="color:var(--text3);font-size:0.7rem;">(2–6 letters, e.g. APP)</span></label>
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
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, defineComponent, h } from 'vue'
import { useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import { useProjectsStore } from '@/store/projects'
import { useAuthStore } from '@/store/auth'
import { statsApi } from '@/api'

// Animated counter component
const AnimatedNumber = defineComponent({
  props: { target: { type: Number, default: 0 } },
  setup(props) {
    const displayed = ref(0)
    onMounted(() => {
      const duration = 900
      const start = performance.now()
      const from = 0
      const to = props.target
      const step = (now) => {
        const t = Math.min((now - start) / duration, 1)
        const ease = 1 - Math.pow(1 - t, 3)
        displayed.value = Math.round(from + (to - from) * ease)
        if (t < 1) requestAnimationFrame(step)
      }
      requestAnimationFrame(step)
    })
    return () => h('span', displayed.value)
  }
})

const router = useRouter()
const projectsStore = useProjectsStore()
const auth = useAuthStore()
const showCreate = ref(false)
const createLoading = ref(false)
const createError = ref('')
const newProject = ref({ name: '', key: '', description: '' })
const stats = ref({ total_projects: 0, open_issues: 0, done_issues: 0, my_open_issues: 0, total_members: 0, recent_issues: [] })
const statsLoading = ref(true)

const projects = computed(() => projectsStore.projects)
const loading = computed(() => projectsStore.loading)
const firstName = computed(() => auth.user?.full_name?.split(' ')[0] || 'there')
const greeting = computed(() => {
  const h = new Date().getHours()
  return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening'
})

const projectColors = ['#10b981','#00d97e','#ff8c42','#ffd166','#06b6d4','#ff4f6a']

const statCards = computed(() => [
  { label: 'Total Projects', value: stats.value.total_projects ?? projects.value.length, sub: 'Active workspaces',     color: '#10b981', barPct: 100, up: false },
  { label: 'Open Issues',    value: stats.value.open_issues,    sub: 'Across all projects',  color: '#ff8c42', barPct: 70,  up: false },
  { label: 'Completed',      value: stats.value.done_issues,    sub: '↑ All time',           color: '#00d97e', barPct: 55,  up: true  },
  { label: 'Assigned to Me', value: stats.value.my_open_issues, sub: 'Open issues',          color: '#ffd166', barPct: 40,  up: false },
])

function dotStyle(key) {
  const i = key.charCodeAt(0) % projectColors.length
  const c = projectColors[i]
  return `background:${c}22;color:${c};`
}
function progressPct(idx) { return 20 + (idx * 23) % 65 }
function myRole(project) {
  if (!auth.user) return 'member'
  const m = project.members.find(m => m.user.id === auth.user.id)
  return m?.role || (project.owner_id === auth.user.id ? 'owner' : 'member')
}
function statusLabel(s) {
  return { backlog: 'Backlog', todo: 'To Do', in_progress: 'In Progress', in_review: 'In Review', done: 'Done' }[s] || s
}

onMounted(async () => {
  await projectsStore.fetchProjects()
  try {
    const r = await statsApi.dashboard()
    stats.value = r.data
  } catch (e) { console.error(e) }
  finally { statsLoading.value = false }
})

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
/* ── Layout ─────────────────────────────────────────────────────────────────── */
.app-shell { display: flex; flex-direction: column; min-height: 100vh; background: var(--bg); }
.shell-body { display: flex; flex: 1; overflow: hidden; height: calc(100vh - 52px); }

/* ── Animations ─────────────────────────────────────────────────────────────── */
.sidebar-animate {
  animation: sidebarIn 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes sidebarIn {
  from { opacity: 0; transform: translateX(-20px); }
  to   { opacity: 1; transform: translateX(0); }
}

.anim-fade-down {
  animation: fadeDown 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
  animation-delay: var(--delay, 0.1s);
}
@keyframes fadeDown {
  from { opacity: 0; transform: translateY(-14px); }
  to   { opacity: 1; transform: translateY(0); }
}

.anim-fade-in {
  opacity: 0;
  animation: fadeIn 0.4s ease forwards;
  animation-delay: var(--delay, 0s);
}
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.anim-slide-up {
  opacity: 0;
  animation: slideUp 0.45s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: var(--delay, 0s);
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(18px); }
  to   { opacity: 1; transform: translateY(0); }
}

.anim-bar {
  width: 0 !important;
  animation: barGrow 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  animation-delay: var(--delay, 0.4s);
}
@keyframes barGrow {
  from { width: 0 !important; }
  to   { width: var(--bar-width) !important; }
}

/* Modal pop transition */
.modal-pop-enter-active { animation: modalIn 0.25s cubic-bezier(0.34, 1.56, 0.64, 1); }
.modal-pop-leave-active { animation: modalIn 0.15s ease reverse; }
@keyframes modalIn {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to   { opacity: 1; transform: scale(1) translateY(0); }
}

/* ── Sidebar ────────────────────────────────────────────────────────────────── */
.sidebar {
  width: 220px; flex-shrink: 0; background: var(--bg2); border-right: 1px solid var(--border);
  display: flex; flex-direction: column; padding: 1rem 0.75rem; overflow-y: auto; gap: 2px;
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
.sidebar-item.active { background: rgba(16,185,129,0.15); color: var(--accent2); }
.sidebar-add { color: var(--text3); font-size: 0.8rem; }
.icon { font-size: 0.9rem; width: 18px; text-align: center; }
.badge { margin-left: auto; background: var(--accent); color: #fff; font-size: 0.65rem; font-weight: 700; padding: 1px 6px; border-radius: 10px; }
.project-dot { width: 22px; height: 22px; border-radius: 5px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 0.6rem; font-weight: 700; font-family: var(--font-mono); }
.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* ── Content ────────────────────────────────────────────────────────────────── */
.content { flex: 1; overflow-y: auto; padding: 1.75rem 2rem; }
.dash-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.5rem; }
.dash-title { font-family: var(--font-display); font-size: 1.5rem; font-weight: 700; letter-spacing: -0.03em; color: var(--text); }
.dash-sub { font-size: 0.85rem; color: var(--text2); margin-top: 3px; }

/* ── Stat Cards ─────────────────────────────────────────────────────────────── */
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 1.75rem; }
.stat-card {
  background: var(--bg2); border: 1px solid var(--border); border-radius: 10px;
  padding: 1.1rem 1.25rem; position: relative; overflow: hidden;
  transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
  cursor: default;
}
.stat-card:hover { border-color: var(--border2); transform: translateY(-2px); box-shadow: 0 6px 24px rgba(0,0,0,0.2); }
.stat-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text3); font-weight: 500; margin-bottom: 0.4rem; }
.stat-value { font-family: var(--font-display); font-size: 2rem; font-weight: 800; color: var(--text); letter-spacing: -0.03em; line-height: 1; min-height: 1em; }
.stat-skeleton { display: inline-block; width: 48px; height: 1em; background: var(--bg3); border-radius: 4px; animation: pulse 1.5s ease-in-out infinite; }
.stat-change { font-size: 0.72rem; color: var(--text3); margin-top: 4px; }
.stat-change.up { color: var(--green); }
.stat-bar { position: absolute; bottom: 0; left: 0; right: 0; height: 3px; }
.stat-bar-fill { height: 100%; }

/* ── Main grid ──────────────────────────────────────────────────────────────── */
.main-grid { display: grid; grid-template-columns: 1fr 320px; gap: 1.5rem; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.85rem; }
.section-title { font-size: 0.85rem; font-weight: 600; color: var(--text); }

/* ── Project Cards ──────────────────────────────────────────────────────────── */
.projects-list { display: flex; flex-direction: column; gap: 10px; }
.project-card {
  background: var(--bg2); border: 1px solid var(--border); border-radius: 10px;
  padding: 1.1rem; text-decoration: none; display: block; position: relative; overflow: hidden;
  transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}
.project-card:hover { border-color: var(--border2); transform: translateY(-2px); box-shadow: 0 6px 24px rgba(0,0,0,0.2); }
.project-top-bar { position: absolute; top: 0; left: 0; right: 0; height: 2px; background: var(--accent-color, var(--accent)); }
.project-key-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4rem; }
.project-key { font-family: var(--font-mono); font-size: 0.68rem; color: var(--text3); }
.member-count { font-size: 0.68rem; color: var(--text3); }
.project-name { font-size: 0.92rem; font-weight: 600; color: var(--text); margin-bottom: 0.25rem; }
.project-desc { font-size: 0.78rem; color: var(--text2); line-height: 1.5; margin-bottom: 0.5rem; display: -webkit-box; -webkit-line-clamp: 1; -webkit-box-orient: vertical; overflow: hidden; }
.progress-wrap { display: flex; align-items: center; gap: 8px; margin: 0.6rem 0 0.7rem; }
.progress-bar { flex: 1; height: 4px; background: var(--bg3); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 4px; }
.progress-label { font-size: 0.65rem; color: var(--text3); font-family: var(--font-mono); flex-shrink: 0; }
.project-footer { display: flex; align-items: center; }
.role-chip { font-size: 0.65rem; font-weight: 600; padding: 2px 8px; border-radius: 10px; text-transform: capitalize; }
.role-owner  { background: rgba(255,209,102,0.15); color: #ffd166; }
.role-admin  { background: rgba(16,185,129,0.15); color: var(--accent2); }
.role-member { background: rgba(0,217,126,0.12); color: #00d97e; }
.role-viewer { background: rgba(144,144,176,0.12); color: var(--text2); }
.member-stack { display: flex; margin-left: auto; }
.member-chip { width: 22px; height: 22px; border-radius: 50%; background: var(--accent); border: 2px solid var(--bg2); display: flex; align-items: center; justify-content: center; font-size: 0.62rem; font-weight: 700; color: #fff; margin-left: -6px; }
.member-chip:first-child { margin-left: 0; }
.member-more { background: var(--bg3); color: var(--text3); font-size: 0.58rem; }

/* ── Activity feed ──────────────────────────────────────────────────────────── */
.activity-list { display: flex; flex-direction: column; gap: 2px; }
.activity-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  border-radius: 8px; text-decoration: none; transition: background 0.12s;
}
.activity-item:hover { background: var(--bg2); }
.activity-type-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.type-bug   { background: var(--red); }
.type-story { background: var(--green); }
.type-task  { background: var(--accent2); }
.type-epic  { background: #06b6d4; }
.activity-body { flex: 1; min-width: 0; }
.activity-key { font-family: var(--font-mono); font-size: 0.68rem; color: var(--text3); }
.activity-title { font-size: 0.8rem; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.activity-right { flex-shrink: 0; }
.status-pill { font-size: 0.65rem; font-weight: 600; padding: 2px 8px; border-radius: 10px; white-space: nowrap; }
.status-todo        { background: rgba(144,144,176,0.15); color: var(--text2); }
.status-in_progress { background: rgba(16,185,129,0.15); color: var(--accent2); }
.status-in_review   { background: rgba(255,209,102,0.15); color: #ffd166; }
.status-done        { background: rgba(0,217,126,0.15); color: var(--green); }

/* ── Misc ───────────────────────────────────────────────────────────────────── */
.skeleton { background: var(--bg2); border-radius: 10px; animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%,100% { opacity:0.4 } 50% { opacity:0.8 } }

.empty-state { text-align: center; padding: 3rem 0; }
.empty-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
.empty-state h2 { font-family: var(--font-display); font-size: 1.2rem; color: var(--text); margin-bottom: 0.4rem; }
.empty-state p { font-size: 0.84rem; color: var(--text2); margin-bottom: 1.25rem; }

/* ── Modal ──────────────────────────────────────────────────────────────────── */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 200; padding: 1rem;
}
.modal {
  background: var(--bg2); border: 1px solid var(--border2); border-radius: 14px;
  padding: 1.75rem; width: 100%; max-width: 420px; box-shadow: 0 32px 64px rgba(0,0,0,0.6);
}
.modal h2 { font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; margin-bottom: 1.25rem; }
.form-group { margin-bottom: 1rem; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 1.25rem; }

/* ── Buttons ────────────────────────────────────────────────────────────────── */
.btn-primary { padding: 8px 16px; border-radius: 8px; background: var(--accent); color: #fff; border: none; cursor: pointer; font-size: 0.83rem; font-weight: 600; font-family: var(--font-body); transition: opacity 0.15s, transform 0.15s; }
.btn-primary:hover { opacity: 0.88; transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
.btn-ghost { padding: 8px 16px; border-radius: 8px; background: transparent; color: var(--text2); border: 1px solid var(--border2); cursor: pointer; font-size: 0.83rem; font-family: var(--font-body); transition: all 0.15s; }
.btn-ghost:hover { color: var(--text); border-color: var(--text3); }

/* ── Phase 4 feature strip ─────────────────────────────────────────────── */
.p4-strip { padding: 0 2rem 2rem; }
.p4-strip-title { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text3); margin-bottom: 0.75rem; }
.p4-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.p4-card { display: flex; flex-direction: column; gap: 4px; padding: 1rem 1.125rem; border-radius: 12px; border: 1px solid var(--border); background: var(--bg2); text-decoration: none; transition: transform 0.15s, border-color 0.2s, box-shadow 0.2s; }
.p4-card:hover { transform: translateY(-3px); border-color: var(--border2); box-shadow: 0 6px 24px rgba(0,0,0,0.2); }
.p4-icon { font-size: 1.2rem; margin-bottom: 4px; }
.p4-label { font-size: 0.85rem; font-weight: 700; color: var(--text); }
.p4-desc { font-size: 0.75rem; color: var(--text3); line-height: 1.4; }
.p4-ai { border-color: rgba(6,182,212,0.2); background: linear-gradient(135deg, rgba(6,182,212,0.05) 0%, rgba(16,185,129,0.05) 100%); }
.p4-ai:hover { border-color: rgba(6,182,212,0.4); box-shadow: 0 6px 24px rgba(6,182,212,0.15); }
.p4-ai .p4-icon { color: #06b6d4; }
.p4-ai .p4-label { color: #06b6d4; }
.p4-org { border-color: rgba(0,217,126,0.2); background: rgba(0,217,126,0.04); }
.p4-org:hover { border-color: rgba(0,217,126,0.35); box-shadow: 0 6px 24px rgba(0,217,126,0.12); }
.p4-import { border-color: rgba(16,185,129,0.2); background: rgba(16,185,129,0.04); }
.p4-import:hover { border-color: rgba(16,185,129,0.35); box-shadow: 0 6px 24px rgba(16,185,129,0.12); }
/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .shell-body { flex-direction: column; }
  .sidebar { width: 100%; height: auto; flex-direction: row; flex-wrap: wrap; border-right: none; border-bottom: 1px solid var(--border); padding: 0.5rem; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .main-grid { grid-template-columns: 1fr; }
  .p4-cards { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .stats-row { grid-template-columns: 1fr; }
  .p4-cards { grid-template-columns: 1fr; }
  .content { padding: 1rem; }
  .dash-header { flex-direction: column; align-items: flex-start; gap: 8px; }
  .p4-strip { padding: 0 1rem 1rem; }
}
</style>
