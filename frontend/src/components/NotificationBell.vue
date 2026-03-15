<template>
  <div class="notif-wrap" ref="wrapRef">
    <!-- Bell button -->
    <button class="bell-btn" @click="toggle" :class="{ active: open }">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
      <span v-if="store.unreadCount > 0" class="badge" :class="{ bump: bumping }">
        {{ store.unreadCount > 99 ? '99+' : store.unreadCount }}
      </span>
    </button>

    <!-- Dropdown panel -->
    <Transition name="notif-drop">
      <div v-if="open" class="notif-panel">
        <div class="panel-header">
          <span class="panel-title">Notifications</span>
          <div class="panel-actions">
            <button v-if="store.unreadCount > 0" class="mark-all-btn" @click="markAll">
              Mark all read
            </button>
          </div>
        </div>

        <!-- Filter tabs -->
        <div class="filter-tabs">
          <button :class="{ active: tab === 'all' }"   @click="tab = 'all'">All</button>
          <button :class="{ active: tab === 'unread' }" @click="tab = 'unread'">
            Unread
            <span v-if="store.unreadCount" class="tab-badge">{{ store.unreadCount }}</span>
          </button>
        </div>

        <div v-if="store.loading" class="notif-list">
          <div v-for="i in 5" :key="i" class="notif-skeleton"></div>
        </div>

        <div v-else-if="filtered.length === 0" class="empty-notifs">
          <div class="empty-icon">🔔</div>
          <p>{{ tab === 'unread' ? 'No unread notifications' : "You're all caught up!" }}</p>
        </div>

        <div v-else class="notif-list" ref="listRef">
          <component
            :is="n.link ? 'router-link' : 'div'"
            v-for="n in filtered"
            :key="n.id"
            :to="n.link || undefined"
            class="notif-item"
            :class="{ unread: !n.read }"
            @click="handleClick(n)"
          >
            <div class="notif-icon" :class="`type-${n.type}`">{{ typeIcon(n.type) }}</div>
            <div class="notif-body">
              <div class="notif-title">{{ n.title }}</div>
              <div v-if="n.body" class="notif-sub">{{ n.body }}</div>
              <div class="notif-time">{{ timeAgo(n.created_at) }}</div>
            </div>
            <div v-if="!n.read" class="unread-dot"></div>
          </component>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useNotificationsStore } from '@/store/notifications'
import { useWsStore } from '@/store/ws'

const store = useNotificationsStore()
const ws    = useWsStore()
const open  = ref(false)
const tab   = ref('all')
const wrapRef = ref(null)
const bumping = ref(false)

const filtered = computed(() =>
  tab.value === 'unread'
    ? store.notifications.filter(n => !n.read)
    : store.notifications
)

function toggle() {
  open.value = !open.value
  if (open.value) store.fetchNotifications()
}

function handleClick(n) {
  if (!n.read) store.markRead(n.id)
  open.value = false
}

async function markAll() {
  await store.markAllRead()
}

// Close on outside click
function onOutsideClick(e) {
  if (wrapRef.value && !wrapRef.value.contains(e.target)) open.value = false
}
onMounted(() => {
  document.addEventListener('mousedown', onOutsideClick)
  store.fetchNotifications()

  // Live notifications via WS
  ws.on('notification', (data) => {
    store.pushLive(data)
    // bump animation
    bumping.value = false
    requestAnimationFrame(() => { bumping.value = true })
    setTimeout(() => { bumping.value = false }, 500)
  })
})
onBeforeUnmount(() => document.removeEventListener('mousedown', onOutsideClick))

function typeIcon(type) {
  const icons = {
    assigned:         '👤',
    commented:        '💬',
    mentioned:        '@',
    status_changed:   '🔄',
    added_to_project: '🎉',
    role_changed:     '🔑',
    sprint_started:   '🚀',
    sprint_completed: '✅',
  }
  return icons[type] || '🔔'
}

function timeAgo(iso) {
  if (!iso) return ''
  const diff = (Date.now() - new Date(iso)) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}
</script>

<style scoped>
.notif-wrap { position: relative; }

/* ── Bell button ─────────────────────────────────────────────────────────── */
.bell-btn {
  position: relative;
  width: 34px; height: 34px; border-radius: 8px;
  background: transparent; border: 1px solid transparent;
  color: var(--text2); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.bell-btn:hover, .bell-btn.active {
  background: rgba(255,255,255,0.07);
  border-color: var(--border);
  color: var(--text);
}
.badge {
  position: absolute; top: 2px; right: 2px;
  min-width: 16px; height: 16px; border-radius: 8px;
  background: var(--red); color: #fff;
  font-size: 0.6rem; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  padding: 0 3px; pointer-events: none;
  border: 2px solid var(--bg2);
}
.badge.bump { animation: badgeBump 0.4s cubic-bezier(0.36, 0.07, 0.19, 0.97); }
@keyframes badgeBump {
  0%,100% { transform: scale(1) rotate(0); }
  25%     { transform: scale(1.4) rotate(-8deg); }
  75%     { transform: scale(1.2) rotate(6deg); }
}

/* ── Panel ───────────────────────────────────────────────────────────────── */
.notif-panel {
  position: absolute; top: calc(100% + 8px); right: 0;
  width: 360px; max-height: 520px;
  background: var(--bg2); border: 1px solid var(--border2);
  border-radius: 12px; box-shadow: 0 24px 48px rgba(0,0,0,0.5);
  display: flex; flex-direction: column; overflow: hidden;
  z-index: 9999;
}

.notif-drop-enter-active { animation: dropIn 0.2s cubic-bezier(0.22, 1, 0.36, 1); }
.notif-drop-leave-active { animation: dropIn 0.12s ease reverse; }
@keyframes dropIn {
  from { opacity: 0; transform: translateY(-8px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0)   scale(1); }
}

.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px 0; flex-shrink: 0;
}
.panel-title { font-size: 0.9rem; font-weight: 700; color: var(--text); }
.mark-all-btn {
  font-size: 0.72rem; color: var(--accent2); background: none; border: none;
  cursor: pointer; padding: 2px 6px; border-radius: 4px; transition: background 0.15s;
}
.mark-all-btn:hover { background: rgba(16,185,129,0.12); }

.filter-tabs {
  display: flex; gap: 4px; padding: 10px 16px 0; flex-shrink: 0;
}
.filter-tabs button {
  display: flex; align-items: center; gap: 5px;
  font-size: 0.76rem; font-weight: 600; padding: 5px 10px; border-radius: 6px;
  background: none; border: none; color: var(--text2); cursor: pointer; transition: all 0.15s;
}
.filter-tabs button.active { background: rgba(16,185,129,0.15); color: var(--accent2); }
.filter-tabs button:hover:not(.active) { background: rgba(255,255,255,0.05); color: var(--text); }
.tab-badge {
  background: var(--accent); color: #fff;
  font-size: 0.6rem; padding: 0 5px; border-radius: 8px; min-width: 16px; text-align: center;
}

/* ── List ─────────────────────────────────────────────────────────────────── */
.notif-list {
  flex: 1; overflow-y: auto; padding: 8px 8px;
  scrollbar-width: thin;
}

.notif-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 10px; border-radius: 8px; cursor: pointer;
  text-decoration: none; transition: background 0.12s;
  position: relative;
}
.notif-item:hover { background: rgba(255,255,255,0.05); }
.notif-item.unread { background: rgba(16,185,129,0.07); }
.notif-item.unread:hover { background: rgba(16,185,129,0.12); }

.notif-icon {
  width: 32px; height: 32px; border-radius: 8px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.9rem; font-weight: 700;
}
.type-assigned         { background: rgba(16,185,129,0.15); }
.type-commented        { background: rgba(0,217,126,0.12); }
.type-mentioned        { background: rgba(255,209,102,0.15); color: #ffd166; font-size: 0.75rem; }
.type-status_changed   { background: rgba(255,140,66,0.15); }
.type-added_to_project { background: rgba(0,217,126,0.12); }
.type-role_changed     { background: rgba(6,182,212,0.15); }
.type-sprint_started   { background: rgba(16,185,129,0.15); }
.type-sprint_completed { background: rgba(0,217,126,0.12); }

.notif-body  { flex: 1; min-width: 0; }
.notif-title { font-size: 0.8rem; font-weight: 600; color: var(--text); line-height: 1.4; }
.notif-sub   { font-size: 0.73rem; color: var(--text2); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.notif-time  { font-size: 0.68rem; color: var(--text3); margin-top: 3px; }

.unread-dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--accent);
  flex-shrink: 0; margin-top: 4px;
}

.notif-skeleton {
  height: 52px; border-radius: 8px; background: var(--bg3); margin-bottom: 4px;
  animation: pulse 1.4s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:.4} 50%{opacity:.8} }

.empty-notifs {
  text-align: center; padding: 2.5rem 1rem; color: var(--text2);
}
.empty-notifs .empty-icon { font-size: 2rem; margin-bottom: 0.5rem; }
.empty-notifs p { font-size: 0.82rem; }
</style>
