/**
 * Global WebSocket store.
 * Connects once per session and pipes events into the relevant Pinia stores.
 * Usage:  wsStore.connect(projectId?)   wsStore.disconnect()
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useWsStore = defineStore('ws', () => {
  const connected    = ref(false)
  const projectId    = ref(null)
  let   _ws          = null
  let   _pingInterval = null
  let   _handlers    = {}   // event -> [fn]

  function on(event, fn) {
    if (!_handlers[event]) _handlers[event] = []
    _handlers[event].push(fn)
  }

  function off(event, fn) {
    if (!_handlers[event]) return
    _handlers[event] = _handlers[event].filter(h => h !== fn)
  }

  function _emit(event, data) {
    ;(_handlers[event] || []).forEach(fn => fn(data))
    ;(_handlers['*'] || []).forEach(fn => fn(event, data))
  }

  function connect(pid = null) {
    const token = localStorage.getItem('token')
    if (!token) return
    // Don't reconnect if already connected to the same project
    if (_ws && connected.value && projectId.value === pid) return

    disconnect()
    projectId.value = pid

    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    const host  = location.host
    const qs    = pid ? `token=${token}&project_id=${pid}` : `token=${token}`
    _ws = new WebSocket(`${proto}://${host}/api/ws?${qs}`)

    _ws.onopen = () => {
      connected.value = true
      _pingInterval = setInterval(() => {
        if (_ws?.readyState === WebSocket.OPEN) _ws.send('ping')
      }, 25000)
    }

    _ws.onmessage = ({ data }) => {
      if (data === 'pong') return
      try {
        const msg = JSON.parse(data)
        _emit(msg.event, msg.data)
      } catch { /* ignore malformed */ }
    }

    _ws.onclose = () => {
      connected.value = false
      clearInterval(_pingInterval)
      // Auto-reconnect after 3s
      setTimeout(() => {
        if (!connected.value) connect(projectId.value)
      }, 3000)
    }

    _ws.onerror = () => _ws?.close()
  }

  function disconnect() {
    clearInterval(_pingInterval)
    if (_ws) {
      _ws.onclose = null  // prevent auto-reconnect on manual disconnect
      _ws.close()
      _ws = null
    }
    connected.value = false
  }

  return { connected, projectId, connect, disconnect, on, off }
})
