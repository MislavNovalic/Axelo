<template>
  <nav class="topbar">
    <router-link to="/" class="topbar-logo">
      <div class="logo-mark">A</div>
      <span class="logo-name">Axelo</span>
    </router-link>

    <div class="topbar-nav">
      <router-link to="/" class="nav-link" :class="{ active: route.name === 'Dashboard' }">Dashboard</router-link>
      <router-link to="/calendar" class="nav-link" :class="{ active: route.name === 'Calendar' }">Calendar</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}`" class="nav-link" :class="{ active: route.name === 'Board' }">Board</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/backlog`" class="nav-link" :class="{ active: route.name === 'Backlog' }">Backlog</router-link>
      <router-link v-if="currentProject" :to="`/projects/${currentProject.id}/team`" class="nav-link" :class="{ active: route.name === 'Team' }">Team</router-link>
    </div>

    <div v-if="currentProject" class="project-breadcrumb">
      <span class="crumb-sep">/</span>
      <span class="crumb-name">{{ currentProject.name }}</span>
      <span class="project-key-badge">{{ currentProject.key }}</span>
    </div>

    <div class="topbar-right">
      <button class="btn-sm ghost" @click="$emit('new-project')">+ Project</button>
      <button class="btn-sm primary" @click="$emit('new-issue')">+ Issue</button>

      <!-- Theme toggle -->
      <button class="theme-toggle" @click="toggleTheme" :title="isDark ? 'Switch to Light' : 'Switch to Dark'">
        <span v-if="isDark">☀️</span>
        <span v-else>🌙</span>
      </button>

      <div class="avatar-wrap" ref="avatarRef">
        <div class="user-avatar" @click="menuOpen = !menuOpen">{{ initials }}</div>
        <div class="user-dropdown" :class="{ show: menuOpen }">
          <div class="dropdown-user">
            <div class="dropdown-name">{{ user?.full_name }}</div>
            <div class="dropdown-email">{{ user?.email }}</div>
          </div>
          <div class="dropdown-divider"></div>
          <div class="dropdown-item">⚙ Settings</div>
          <div class="dropdown-item">👥 Team</div>
          <div class="dropdown-divider"></div>
          <div class="dropdown-item danger" @click="handleLogout">↩ Sign out</div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { onClickOutside } from '@vueuse/core'
import { useAuthStore } from '@/store/auth'
import { useProjectsStore } from '@/store/projects'

defineEmits(['new-project', 'new-issue'])
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const projectsStore = useProjectsStore()
const menuOpen = ref(false)
const avatarRef = ref(null)
const isDark = ref(true)

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
})

function toggleTheme() {
  isDark.value = !isDark.value
  localStorage.setItem('axelo-theme', isDark.value ? 'dark' : 'light')
  applyTheme()
}

function applyTheme() {
  const root = document.documentElement
  if (isDark.value) {
    root.style.setProperty('--bg',           '#07070d')
    root.style.setProperty('--bg2',          '#0e0e18')
    root.style.setProperty('--bg3',          '#13131f')
    root.style.setProperty('--border',       'rgba(255,255,255,0.07)')
    root.style.setProperty('--border2',      'rgba(255,255,255,0.12)')
    root.style.setProperty('--text',         '#f0f0f8')
    root.style.setProperty('--text2',        '#9090b0')
    root.style.setProperty('--text3',        '#55556a')
    root.style.setProperty('--accent',       '#5c4fff')
    root.style.setProperty('--accent2',      '#7c6fff')
    root.style.setProperty('--accent-glow',  'rgba(92,79,255,0.35)')
  } else {
    root.style.setProperty('--bg',           '#f4f4f8')
    root.style.setProperty('--bg2',          '#ffffff')
    root.style.setProperty('--bg3',          '#eaeaf2')
    root.style.setProperty('--border',       'rgba(0,0,0,0.08)')
    root.style.setProperty('--border2',      'rgba(0,0,0,0.14)')
    root.style.setProperty('--text',         '#0f0f1a')
    root.style.setProperty('--text2',        '#4a4a6a')
    root.style.setProperty('--text3',        '#9090aa')
    root.style.setProperty('--accent',       '#5c4fff')
    root.style.setProperty('--accent2',      '#4438dd')
    root.style.setProperty('--accent-glow',  'rgba(92,79,255,0.2)')
  }
}

function handleLogout() {
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
.topbar-logo {
  display: flex; align-items: center; gap: 8px;
  text-decoration: none; margin-right: 0.5rem;
}
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
  color: var(--text2); text-decoration: none;
  transition: color 0.15s, background 0.15s;
}
.nav-link:hover, .nav-link.active { color: var(--text); background: rgba(128,128,200,0.1); }
.project-breadcrumb { display: flex; align-items: center; gap: 8px; }
.crumb-sep { color: var(--text3); font-size: 0.9rem; }
.crumb-name { font-size: 0.85rem; font-weight: 500; color: var(--text2); }
.project-key-badge {
  font-family: var(--font-mono); font-size: 0.68rem; color: var(--accent2);
  background: rgba(92,79,255,0.1); padding: 2px 7px; border-radius: 4px;
}
.topbar-right { margin-left: auto; display: flex; align-items: center; gap: 10px; }

.theme-toggle {
  width: 32px; height: 32px; border-radius: 8px;
  border: 1px solid var(--border); background: var(--bg3);
  cursor: pointer; font-size: 15px;
  display: flex; align-items: center; justify-content: center;
  transition: border-color 0.15s, background 0.15s;
}
.theme-toggle:hover { border-color: var(--accent); background: rgba(92,79,255,0.08); }

.avatar-wrap { position: relative; }
.user-avatar {
  width: 30px; height: 30px; border-radius: 50%; background: var(--accent);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem; font-weight: 700; color: #fff; cursor: pointer;
  transition: box-shadow 0.15s;
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
.dropdown-item {
  padding: 7px 10px; border-radius: 6px; font-size: 0.82rem;
  color: var(--text2); cursor: pointer; transition: all 0.15s;
}
.dropdown-item:hover { background: rgba(128,128,200,0.08); color: var(--text); }
.dropdown-item.danger:hover { background: rgba(255,79,106,0.1); color: var(--red); }
</style>
