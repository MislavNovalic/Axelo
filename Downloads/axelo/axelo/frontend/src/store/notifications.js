import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { notificationsApi } from '@/api'

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref([])
  const loading = ref(false)

  const unreadCount = computed(() => notifications.value.filter(n => !n.read_at).length)

  async function fetchNotifications(unreadOnly = false) {
    loading.value = true
    try {
      const res = await notificationsApi.list({ unread_only: unreadOnly })
      notifications.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function markRead(id) {
    const res = await notificationsApi.markRead(id)
    const idx = notifications.value.findIndex(n => n.id === id)
    if (idx !== -1) notifications.value[idx] = res.data
  }

  async function markAllRead() {
    await notificationsApi.markAllRead()
    notifications.value = notifications.value.map(n => ({ ...n, read_at: new Date().toISOString() }))
  }

  // Called from WebSocket handler when a new notification arrives
  function pushNotification(notif) {
    notifications.value.unshift(notif)
  }

  return { notifications, loading, unreadCount, fetchNotifications, markRead, markAllRead, pushNotification }
})
