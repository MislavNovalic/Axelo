import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref([])
  const loading       = ref(false)

  const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

  async function fetchNotifications() {
    loading.value = true
    try {
      const res = await api.get('/notifications?limit=40')
      notifications.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function markRead(id) {
    await api.patch(`/notifications/${id}/read`)
    const n = notifications.value.find(n => n.id === id)
    if (n) n.read = true
  }

  async function markAllRead() {
    await api.post('/notifications/read-all')
    notifications.value.forEach(n => { n.read = true })
  }

  /** Called by the WS store when a live notification arrives */
  function pushLive(data) {
    // prepend and cap at 40
    notifications.value.unshift({ ...data, read: false })
    if (notifications.value.length > 40) notifications.value.pop()
  }

  return { notifications, loading, unreadCount, fetchNotifications, markRead, markAllRead, pushLive }
})
