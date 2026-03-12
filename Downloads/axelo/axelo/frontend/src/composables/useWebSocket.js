import { ref, onUnmounted } from 'vue'

const RECONNECT_DELAY = 3000
const POLL_INTERVAL = 30000 // fallback polling interval

/**
 * WebSocket composable for real-time project collaboration.
 *
 * Usage:
 *   const { connected } = useWebSocket(projectId, token, {
 *     'issue.updated': (data) => { ... },
 *     'issue.created': (data) => { ... },
 *   })
 *
 * Automatically reconnects on disconnect.
 * Falls back to polling trigger (emits 'poll' event) if WS is unavailable.
 */
export function useWebSocket(projectId, token, handlers = {}) {
  const connected = ref(false)
  let ws = null
  let reconnectTimer = null
  let pollTimer = null
  let destroyed = false

  function connect() {
    if (destroyed) return

    const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${protocol}://${location.host}/ws/${projectId}?token=${encodeURIComponent(token)}`

    try {
      ws = new WebSocket(url)
    } catch {
      schedulePoll()
      return
    }

    ws.onopen = () => {
      connected.value = true
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
    }

    ws.onmessage = (event) => {
      try {
        const { event: name, data } = JSON.parse(event.data)
        if (name === 'pong') return
        if (handlers[name]) handlers[name](data)
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = () => {
      connected.value = false
      ws = null
      if (!destroyed) {
        scheduleReconnect()
      }
    }

    ws.onerror = () => {
      ws?.close()
    }
  }

  function scheduleReconnect() {
    if (destroyed) return
    reconnectTimer = setTimeout(connect, RECONNECT_DELAY)
  }

  function schedulePoll() {
    if (pollTimer || destroyed) return
    pollTimer = setInterval(() => {
      if (handlers['poll']) handlers['poll']()
    }, POLL_INTERVAL)
  }

  function send(data) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }

  function ping() {
    send('ping')
  }

  // Keepalive ping every 25s to prevent idle timeout
  const pingTimer = setInterval(ping, 25000)

  connect()

  onUnmounted(() => {
    destroyed = true
    clearTimeout(reconnectTimer)
    clearInterval(pollTimer)
    clearInterval(pingTimer)
    ws?.close()
  })

  return { connected, send }
}
