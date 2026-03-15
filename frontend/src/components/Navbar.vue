<template>
  <nav class="topbar">
    <button class="hamburger" @click="mobileMenuOpen = !mobileMenuOpen">☰</button>

    <router-link to="/" class="topbar-logo">
      <div class="logo-mark">A</div>
      <span class="logo-name">Axelo</span>
    </router-link>

    <div class="topbar-nav">
      <router-link to="/" class="nav-link" :class="{ active: route.name === 'Dashboard' }">Dashboard</router-link>
      <router-link to="/calendar" class="nav-link" :class="{ active: route.name === 'Calendar' }">Calendar</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}`" class="nav-link" :class="{ active: route.name === 'Board' }">Board</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/backlog`" class="nav-link" :class="{ active: route.name === 'Backlog' }">Backlog</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/reports`" class="nav-link" :class="{ active: route.name === 'Reports' }">Reports</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/roadmap`" class="nav-link" :class="{ active: route.name === 'Roadmap' }">Roadmap</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/ai/sprint-planner`" class="nav-link ai-link" :class="{ active: route.name === 'AiPlanner' }">✦ AI Planner</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/import`" class="nav-link" :class="{ active: route.name === 'Importer' }">Import</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/settings`" class="nav-link" :class="{ active: route.name === 'Settings' }">Settings</router-link>
    </div>

    <!-- Mobile slide-down menu -->
    <div class="mobile-menu" :class="{ open: mobileMenuOpen }">
      <router-link to="/" class="nav-link" :class="{ active: route.name === 'Dashboard' }">Dashboard</router-link>
      <router-link to="/calendar" class="nav-link" :class="{ active: route.name === 'Calendar' }">Calendar</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}`" class="nav-link" :class="{ active: route.name === 'Board' }">Board</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/backlog`" class="nav-link" :class="{ active: route.name === 'Backlog' }">Backlog</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/reports`" class="nav-link" :class="{ active: route.name === 'Reports' }">Reports</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/roadmap`" class="nav-link" :class="{ active: route.name === 'Roadmap' }">Roadmap</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/ai/sprint-planner`" class="nav-link ai-link" :class="{ active: route.name === 'AiPlanner' }">✦ AI Planner</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/import`" class="nav-link" :class="{ active: route.name === 'Importer' }">Import</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/settings`" class="nav-link" :class="{ active: route.name === 'Settings' }">Settings</router-link>
      <div v-if="currentProject" class="mobile-breadcrumb">
        <span class="crumb-sep">/</span>
        <span class="crumb-name">{{ currentProject.name }}</span>
        <span class="project-key-badge">{{ currentProject.key }}</span>
      </div>
    </div>

    <div v-if="currentProject" class="project-breadcrumb">
      <span class="crumb-sep">/</span>
      <span class="crumb-name">{{ currentProject.name }}</span>
      <span class="project-key-badge">{{ currentProject.key }}</span>
    </div>

    <!-- Live indicator -->
    <div class="live-indicator" :class="{ connected: wsStore.connected }" title="Real-time sync">
      <span class="live-dot"></span>
      <span class="live-label">{{ wsStore.connected ? 'Live' : 'Offline' }}</span>
    </div>

    <div class="topbar-right">
      <button class="btn-sm ghost" @click="$emit('new-project')">+ Project</button>
      <button class="btn-sm primary" @click="$emit('new-issue')">+ Issue</button>

      <!-- Theme toggle -->
      <button class="theme-toggle" @click="toggleTheme" :title="isDark ? 'Switch to Light' : 'Switch to Dark'">
        <span v-if="isDark">☀️</span>
        <span v-else>🌙</span>
      </button>

      <!-- 🔍 Search trigger (Cmd+K) -->
      <button class="search-trigger" @click="openSearch" title="Search (Ctrl+K)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <span>Search</span>
        <kbd>⌘K</kbd>
      </button>

      <!-- ⌨ Keyboard shortcuts hint -->
      <button class="shortcuts-hint" @click="shortcutsVisible = !shortcutsVisible" title="Keyboard shortcuts (?)">
        <kbd>?</kbd>
      </button>

      <!-- 🔔 Notification Bell -->
      <NotificationBell />

      <div class="avatar-wrap" ref="avatarRef">
        <div class="user-avatar" @click="menuOpen = !menuOpen">{{ initials }}</div>
        <div class="user-dropdown" :class="{ show: menuOpen }">
          <div class="dropdown-user">
            <div class="dropdown-name">{{ user?.full_name }}</div>
            <div class="dropdown-email">{{ user?.email }}</div>
          </div>
          <div class="dropdown-divider"></div>
          <div class="dropdown-item" @click="goToSettings">⚙ Settings</div>
          <div class="dropdown-item">👥 Team</div>
          <div class="dropdown-divider"></div>
          <div class="dropdown-item danger" @click="handleLogout">↩ Sign out</div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { onClickOutside } from '@vueuse/core'
import { useAuthStore } from '@/store/auth'
import { useProjectsStore } from '@/store/projects'
import { useWsStore } from '@/store/ws'
import { shortcutsVisible } from '@/composables/useKeyboardShortcuts'
import NotificationBell from './NotificationBell.vue'

defineEmits(['new-project', 'new-issue'])
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const projectsStore = useProjectsStore()
const wsStore = useWsStore()
const menuOpen = ref(false)
const mobileMenuOpen = ref(false)
const avatarRef = ref(null)
const isDark = ref(true)

watch(() => route.name, () => { mobileMenuOpen.value = false })

const user = computed(() => auth.user)
const currentProject = computed(() => projectsStore.currentProject)
const initials = computed(() =>
  user.value?.full_name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() || '?'
)

onClickOutside(avatarRef, () => { menuOpen.value = false })

onMounted(() => {
  const saved = localStorage.getItem('axelo-theme')
  isDark.value = saved !== 'light'
  applyTheme()
  // Start WebSocket connection (no project room yet — notifications only)
  wsStore.connect(null)
})

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('axelo-theme', isDark.value ? 'dark' : 'light')
  applyTheme()
}

function applyTheme() {
  const root = document.documentElement
  if (isDark.value) {
    root.style.setProperty('--bg',           '#070d09')
    root.style.setProperty('--bg2',          '#0d1610')
    root.style.setProperty('--bg3',          '#111e14')
    root.style.setProperty('--border',       'rgba(255,255,255,0.07)')
    root.style.setProperty('--border2',      'rgba(255,255,255,0.12)')
    root.style.setProperty('--text',         '#f0f8f4')
    root.style.setProperty('--text2',        '#90b09a')
    root.style.setProperty('--text3',        '#4a6455')
    root.style.setProperty('--accent',       '#10b981')
    root.style.setProperty('--accent2',      '#34d399')
    root.style.setProperty('--accent-glow',  'rgba(16,185,129,0.35)')
  } else {
    root.style.setProperty('--bg',           '#f4f4f8')
    root.style.setProperty('--bg2',          '#ffffff')
    root.style.setProperty('--bg3',          '#eaeaf2')
    root.style.setProperty('--border',       'rgba(0,0,0,0.08)')
    root.style.setProperty('--border2',      'rgba(0,0,0,0.14)')
    root.style.setProperty('--text',         '#0f0f1a')
    root.style.setProperty('--text2',        '#4a4a6a')
    root.style.setProperty('--text3',        '#9090aa')
    root.style.setProperty('--accent',       '#10b981')
    root.style.setProperty('--accent2',      '#4438dd')
    root.style.setProperty('--accent-glow',  'rgba(16,185,129,0.2)')
  }
}

function openSearch() {
  // SearchPalette listens for Cmd+K globally — just fire the keyboard event
  document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true, ctrlKey: true, bubbles: true }))
}

function goToSettings() {
  menuOpen.value = false
  if (currentProject.value) router.push(`/projects/${currentProject.value.id}/settings`)
}

function handleLogout() {
  wsStore.disconnect()
  auth.logout()
  projectsStore.currentProject = null
  router.push('/login')
}
</script>

<style scoped>
.topbar {
  height: 52px; flex-shrink: 0;
  background: var(--bg2); border-bottom: 1px solid var(--border);
  display: flex; align-items: center; padding: 0 1.25rem; gap: 0.75rem;
  position: sticky; top: 0; z-index: 100;
}
.topbar-logo { display: flex; align-items: center; gap: 8px; text-decoration: none; margin-right: 0.5rem; }
.logo-mark {
  width: 28px; height: 28px; background: var(--accent); border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-family: var(--font-display); font-weight: 800; font-size: 14px; color: #fff;
  box-shadow: 0 0 16px var(--accent-glow);
}
.logo-name { font-family: var(--font-display); font-size: 1rem; font-weight: 700; letter-spacing: -0.02em; color: var(--text); }
.topbar-nav { display: flex; align-items: center; gap: 2px; }
.nav-link {
  padding: 5px 11px; border-radius: 6px; font-size: 0.83rem;
  color: var(--text2); text-decoration: none; transition: color 0.15s, background 0.15s;
}
.nav-link:hover, .nav-link.active { color: var(--text); background: rgba(128,128,200,0.1); }
.ai-link { color: #06b6d4 !important; }
.ai-link:hover, .ai-link.active { background: rgba(187,92,247,0.12) !important; }
.project-breadcrumb { display: flex; align-items: center; gap: 8px; }
.crumb-sep { color: var(--text3); font-size: 0.9rem; }
.crumb-name { font-size: 0.85rem; font-weight: 500; color: var(--text2); }
.project-key-badge {
  font-family: var(--font-mono); font-size: 0.68rem; color: var(--accent2);
  background: rgba(16,185,129,0.1); padding: 2px 7px; border-radius: 4px;
}

/* ── Live indicator ─────────────────────────────────────────────────────── */
.live-indicator {
  display: flex; align-items: center; gap: 5px;
  padding: 3px 8px; border-radius: 20px;
  border: 1px solid var(--border);
  font-size: 0.68rem; font-weight: 600; color: var(--text3);
  transition: all 0.3s;
}
.live-indicator.connected {
  border-color: rgba(0,217,126,0.3);
  color: #00d97e;
}
.live-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text3); transition: background 0.3s;
}
.live-indicator.connected .live-dot {
  background: #00d97e;
  animation: livePulse 2s ease-in-out infinite;
}
@keyframes livePulse {
  0%,100% { opacity: 1; transform: scale(1); }
  50%     { opacity: 0.5; transform: scale(0.7); }
}

.topbar-right { margin-left: auto; display: flex; align-items: center; gap: 8px; }
.theme-toggle {
  width: 32px; height: 32px; border-radius: 8px;
  border: 1px solid var(--border); background: var(--bg3);
  cursor: pointer; font-size: 15px;
  display: flex; align-items: center; justify-content: center;
  transition: border-color 0.15s, background 0.15s;
}
.theme-toggle:hover { border-color: var(--accent); background: rgba(16,185,129,0.08); }
.avatar-wrap { position: relative; }
.user-avatar {
  width: 30px; height: 30px; border-radius: 50%; background: var(--accent);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem; font-weight: 700; color: #fff; cursor: pointer; transition: box-shadow 0.15s;
}
.user-avatar:hover { box-shadow: 0 0 0 2px var(--accent); }
.user-dropdown {
  display: none; position: absolute; right: 0; top: 40px;
  background: var(--bg2); border: 1px solid var(--border2); border-radius: 10px;
  padding: 6px; width: 188px;
  box-shadow: 0 16px 40px rgba(0,0,0,0.3); z-index: 200;
}
.user-dropdown.show { display: block; }
.dropdown-user { padding: 7px 10px; }
.dropdown-name { font-size: 0.83rem; font-weight: 500; color: var(--text); }
.dropdown-email { font-size: 0.72rem; color: var(--text3); margin-top: 1px; }
.dropdown-divider { height: 1px; background: var(--border); margin: 4px 0; }
.dropdown-item { padding: 7px 10px; border-radius: 6px; font-size: 0.82rem; color: var(--text2); cursor: pointer; transition: all 0.15s; }
.dropdown-item:hover { background: rgba(128,128,200,0.08); color: var(--text); }
.dropdown-item.danger:hover { background: rgba(255,79,106,0.1); color: var(--red); }

/* Buttons */
.btn-sm { padding: 6px 12px; border-radius: 6px; font-size: 0.78rem; font-weight: 600; cursor: pointer; font-family: var(--font-body); transition: all 0.15s; }
.btn-sm.primary { background: var(--accent); color: #fff; border: none; }
.btn-sm.primary:hover { opacity: 0.88; }
.btn-sm.ghost { background: transparent; color: var(--text2); border: 1px solid var(--border2); }
.btn-sm.ghost:hover { color: var(--text); border-color: var(--text3); }

.search-trigger {
  display: flex; align-items: center; gap: 6px;
  padding: 5px 10px; border-radius: 7px;
  background: var(--bg3); border: 1px solid var(--border2);
  color: var(--text2); cursor: pointer; font-size: 0.75rem;
  font-family: var(--font-body); transition: all 0.15s;
  min-width: 120px;
}
.search-trigger:hover { border-color: var(--accent); color: var(--text); }
.search-trigger kbd {
  background: var(--bg2); border: 1px solid var(--border2);
  border-radius: 3px; padding: 1px 4px; font-size: 0.65rem; color: var(--text3);
}

.shortcuts-hint {
  background: var(--bg3); border: 1px solid var(--border2);
  border-radius: 6px; cursor: pointer; padding: 3px 8px;
  color: var(--text3); transition: all 0.15s;
}
.shortcuts-hint:hover { border-color: var(--accent); color: var(--text); }
.shortcuts-hint kbd { font-size: 0.7rem; }

/* ── Hamburger & Mobile Menu ────────────────────────────────────────────── */
.hamburger {
  display: none; background: none; border: 1px solid var(--border);
  border-radius: 6px; color: var(--text2); cursor: pointer;
  width: 32px; height: 32px; font-size: 1.1rem;
  align-items: center; justify-content: center;
}

.mobile-menu {
  display: none; position: absolute; top: 52px; left: 0; right: 0;
  background: var(--bg2); border-bottom: 1px solid var(--border);
  padding: 0.75rem 1rem; flex-direction: column; gap: 4px; z-index: 99;
}
.mobile-menu.open { display: flex; }
.mobile-menu .nav-link { padding: 8px 12px; border-radius: 8px; font-size: 0.88rem; }
.mobile-breadcrumb { display: flex; align-items: center; gap: 8px; padding: 8px 12px; margin-top: 4px; border-top: 1px solid var(--border); }

@media (max-width: 1024px) {
  .hamburger { display: flex; }
  .topbar-nav { display: none; }
  .project-breadcrumb { display: none; }
  .search-trigger span:not(kbd) { display: none; }
  .search-trigger { min-width: unset; }
  .live-label { display: none; }
}

@media (max-width: 640px) {
  .btn-sm.ghost { display: none; }
  .shortcuts-hint { display: none; }
  .logo-name { display: none; }
}
</style>