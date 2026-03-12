<template>
  <div class="notif-wrap" ref="bellRef">
    <button class="bell-btn" @click="toggleOpen" :title="unreadCount > 0 ? `${unreadCount} unread` : 'Notifications'">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
      <span v-if="unreadCount > 0" class="badge">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
    </button>

    <div class="notif-dropdown" :class="{ show: open }">
      <div class="notif-header">
        <span class="notif-title">Notifications</span>
        <button v-if="unreadCount > 0" class="mark-all-btn" @click="handleMarkAll">Mark all read</button>
      </div>

      <div class="notif-list">
        <div v-if="loading" class="notif-empty">Loading…</div>
        <div v-else-if="!notifications.length" class="notif-empty">No notifications yet</div>
        <div
          v-for="n in notifications.slice(0, 20)"
          :key="n.id"
          class="notif-item"
          :class="{ unread: !n.read_at }"
          @click="handleClick(n)"
        >
          <div class="notif-icon">{{ typeIcon(n.type) }}</div>
          <div class="notif-body">
            <div class="notif-text">{{ formatPayload(n) }}</div>
            <div class="notif-time">{{ formatTime(n.created_at) }}</div>
          </div>
          <div v-if="!n.read_at" class="unread-dot"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { onClickOutside } from '@vueuse/core'
import { useNotificationsStore } from '@/store/notifications'
import { storeToRefs } from 'pinia'
import { formatDistanceToNow } from 'date-fns'

const router = useRouter()
const store = useNotificationsStore()
const { notifications, loading, unreadCount } = storeToRefs(store)

const open = ref(false)
const bellRef = ref(null)

onClickOutside(bellRef, () => { open.value = false })

onMounted(() => store.fetchNotifications())

function toggleOpen() {
  open.value = !open.value
}

function typeIcon(type) {
  if (type === 'issue.assigned') return '👤'
  if (type === 'comment.created') return '💬'
  if (type === 'sprint.started') return '🚀'
  if (type === 'sprint.completed') return '✅'
  return '🔔'
}

function formatPayload(n) {
  const p = n.payload || {}
  if (n.type === 'issue.assigned') return `${p.actor || 'Someone'} assigned you to ${p.issue_key || 'an issue'}`
  if (n.type === 'comment.created') return `${p.actor || 'Someone'} commented on ${p.issue_key}: "${p.body_preview || ''}"`
  if (n.type === 'sprint.started') return `Sprint "${p.sprint_name}" started`
  if (n.type === 'sprint.completed') return `Sprint "${p.sprint_name}" completed`
  return p.message || n.type
}

function formatTime(ts) {
  try {
    return formatDistanceToNow(new Date(ts), { addSuffix: true })
  } catch {
    return ''
  }
}

async function handleClick(n) {
  if (!n.read_at) await store.markRead(n.id)
  open.value = false
  if (n.link) router.push(n.link)
}

async function handleMarkAll() {
  await store.markAllRead()
}
</script>

<style scoped>
.notif-wrap { position: relative; }

.bell-btn {
  width: 34px; height: 34px; border-radius: 8px;
  border: 1px solid var(--border); background: var(--bg3);
  cursor: pointer; color: var(--text2);
  display: flex; align-items: center; justify-content: center;
  position: relative; transition: border-color 0.15s, color 0.15s;
}
.bell-btn:hover { border-color: var(--accent); color: var(--text); }

.badge {
  position: absolute; top: -4px; right: -4px;
  background: #ff4f6a; color: #fff;
  font-size: 0.58rem; font-weight: 700;
  min-width: 16px; height: 16px; border-radius: 100px;
  display: flex; align-items: center; justify-content: center;
  padding: 0 3px; pointer-events: none;
}

.notif-dropdown {
  display: none; position: absolute; right: 0; top: 42px;
  width: 340px; background: var(--bg2);
  border: 1px solid var(--border2); border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0,0,0,0.35); z-index: 300;
  overflow: hidden;
}
.notif-dropdown.show { display: block; }

.notif-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px; border-bottom: 1px solid var(--border);
}
.notif-title { font-size: 0.82rem; font-weight: 600; color: var(--text); }
.mark-all-btn {
  font-size: 0.72rem; color: var(--accent2); background: none;
  border: none; cursor: pointer; padding: 0;
}
.mark-all-btn:hover { text-decoration: underline; }

.notif-list { max-height: 380px; overflow-y: auto; }

.notif-empty { padding: 24px; text-align: center; font-size: 0.8rem; color: var(--text3); }

.notif-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 14px; cursor: pointer;
  transition: background 0.12s; border-bottom: 1px solid var(--border);
}
.notif-item:last-child { border-bottom: none; }
.notif-item:hover { background: rgba(128,128,200,0.06); }
.notif-item.unread { background: rgba(92,79,255,0.04); }

.notif-icon { font-size: 1rem; flex-shrink: 0; margin-top: 1px; }

.notif-body { flex: 1; min-width: 0; }
.notif-text { font-size: 0.78rem; color: var(--text); line-height: 1.4; word-break: break-word; }
.notif-time { font-size: 0.68rem; color: var(--text3); margin-top: 3px; }

.unread-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--accent); flex-shrink: 0; margin-top: 5px;
}
</style>
