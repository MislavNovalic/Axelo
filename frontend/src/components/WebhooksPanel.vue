<template>
  <div class="webhooks-panel">
    <div class="panel-header">
      <div>
        <h3 class="panel-title">Outbound Webhooks</h3>
        <p class="panel-sub">Send real-time event payloads to Slack, Zapier, or any custom endpoint.</p>
      </div>
      <button class="btn-primary" @click="showCreate = true">+ Add Webhook</button>
    </div>

    <!-- Webhook list -->
    <div v-if="hooks.length" class="hook-list">
      <div v-for="hook in hooks" :key="hook.id" class="hook-card">
        <div class="hook-top">
          <div class="hook-url" :title="hook.url">{{ truncate(hook.url, 55) }}</div>
          <div class="hook-controls">
            <button class="btn-ghost" @click="testHook(hook)" title="Send test ping">⚡ Test</button>
            <button class="btn-ghost" @click="showDeliveries(hook)" title="View deliveries">📋</button>
            <button class="btn-toggle" :class="hook.active ? 'on' : 'off'"
              @click="toggleActive(hook)" :title="hook.active ? 'Disable' : 'Enable'">
              {{ hook.active ? 'Active' : 'Paused' }}
            </button>
            <button class="btn-del" @click="removeHook(hook.id)" title="Delete">✕</button>
          </div>
        </div>
        <div class="hook-events">
          <span v-for="ev in hook.events" :key="ev" class="event-chip">{{ ev }}</span>
        </div>
      </div>
    </div>
    <div v-else class="empty-state">No webhooks configured. Add one to integrate with external tools.</div>

    <!-- Create modal -->
    <div v-if="showCreate" class="modal-backdrop" @click.self="showCreate = false">
      <div class="modal">
        <div class="modal-header">
          <h3>Add Webhook</h3>
          <button class="btn-close" @click="showCreate = false">✕</button>
        </div>
        <div class="modal-body">
          <div class="field">
            <label class="field-label">Endpoint URL</label>
            <input v-model="form.url" type="url" class="field-input" placeholder="https://hooks.slack.com/..." />
          </div>
          <div class="field">
            <label class="field-label">Events to send</label>
            <div class="event-checks">
              <label v-for="ev in allEvents" :key="ev" class="ev-check">
                <input type="checkbox" :value="ev" v-model="form.events" />
                <span>{{ ev }}</span>
              </label>
            </div>
          </div>
          <div class="field">
            <label class="field-label">Secret (optional — auto-generated if blank)</label>
            <input v-model="form.secret" type="text" class="field-input" placeholder="Leave blank to auto-generate" />
          </div>
          <transition name="err">
            <div v-if="createError" class="err-msg">{{ createError }}</div>
          </transition>
        </div>
        <div class="modal-footer">
          <button class="btn-ghost" @click="showCreate = false">Cancel</button>
          <button class="btn-primary" @click="createHook" :disabled="!form.url || !form.events.length || creating">
            {{ creating ? 'Creating…' : 'Create' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Deliveries modal -->
    <div v-if="deliveriesHook" class="modal-backdrop" @click.self="deliveriesHook = null">
      <div class="modal modal-wide">
        <div class="modal-header">
          <h3>Deliveries · {{ truncate(deliveriesHook.url, 40) }}</h3>
          <button class="btn-close" @click="deliveriesHook = null">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="deliveries.length" class="delivery-list">
            <div v-for="d in deliveries" :key="d.id" class="delivery-row">
              <span class="d-status" :class="d.status">{{ d.status }}</span>
              <span class="d-event">{{ d.event }}</span>
              <span class="d-code" v-if="d.response_code">{{ d.response_code }}</span>
              <span class="d-attempts">{{ d.attempts }} attempt{{ d.attempts !== 1 ? 's' : '' }}</span>
              <span class="d-date">{{ fmtDate(d.created_at) }}</span>
            </div>
          </div>
          <div v-else class="empty-state">No deliveries yet.</div>
        </div>
      </div>
    </div>

    <!-- Secret reveal after create -->
    <div v-if="newSecret" class="modal-backdrop" @click.self="newSecret = null">
      <div class="modal">
        <div class="modal-header">
          <h3>Webhook Created</h3>
          <button class="btn-close" @click="newSecret = null">✕</button>
        </div>
        <div class="modal-body">
          <p class="secret-note">⚠️ Copy the signing secret now — it won't be shown again.</p>
          <code class="secret-box">{{ newSecret }}</code>
          <button class="btn-outline" @click="copySecret">📋 Copy secret</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { webhooksApi } from '@/api'

const props = defineProps({ projectId: { type: Number, required: true } })

const hooks = ref([])
const showCreate = ref(false)
const creating = ref(false)
const createError = ref('')
const deliveriesHook = ref(null)
const deliveries = ref([])
const newSecret = ref(null)

const allEvents = [
  'issue.created', 'issue.updated', 'issue.deleted',
  'sprint.started', 'sprint.completed', 'member.added',
]

const form = ref({ url: '', events: [], secret: '' })

function truncate(str, n) {
  return str?.length > n ? str.slice(0, n) + '…' : str
}

function fmtDate(iso) {
  return new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function fetchHooks() {
  const res = await webhooksApi.list(props.projectId)
  hooks.value = res.data
}

async function createHook() {
  creating.value = true; createError.value = ''
  try {
    const res = await webhooksApi.create(props.projectId, {
      url: form.value.url,
      events: form.value.events,
      secret: form.value.secret || undefined,
    })
    newSecret.value = res.data.secret
    form.value = { url: '', events: [], secret: '' }
    showCreate.value = false
    await fetchHooks()
  } catch (e) {
    createError.value = e.response?.data?.detail || 'Failed to create webhook'
  } finally { creating.value = false }
}

async function removeHook(id) {
  if (!confirm('Delete this webhook?')) return
  await webhooksApi.delete(props.projectId, id)
  await fetchHooks()
}

async function toggleActive(hook) {
  await webhooksApi.update(props.projectId, hook.id, { active: !hook.active })
  await fetchHooks()
}

async function testHook(hook) {
  await webhooksApi.test(props.projectId, hook.id)
  alert('Test ping queued — check deliveries in a moment.')
}

async function showDeliveries(hook) {
  deliveriesHook.value = hook
  const res = await webhooksApi.deliveries(props.projectId, hook.id)
  deliveries.value = res.data
}

function copySecret() {
  navigator.clipboard.writeText(newSecret.value)
}

onMounted(fetchHooks)
</script>

<style scoped>
.webhooks-panel { padding: 0; }
.panel-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.25rem; gap: 1rem; }
.panel-title { font-size: 1rem; font-weight: 700; color: var(--text); margin-bottom: 0.2rem; }
.panel-sub { font-size: 0.82rem; color: var(--text2); }
.hook-list { display: flex; flex-direction: column; gap: 8px; }
.hook-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }
.hook-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; gap: 8px; }
.hook-url { font-family: var(--font-mono); font-size: 0.8rem; color: var(--text2); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.hook-controls { display: flex; align-items: center; gap: 5px; flex-shrink: 0; }
.hook-events { display: flex; flex-wrap: wrap; gap: 5px; }
.event-chip { font-size: 0.72rem; background: rgba(16,185,129,0.1); color: var(--accent2); border: 1px solid rgba(16,185,129,0.2); border-radius: 4px; padding: 2px 7px; font-family: var(--font-mono); }
.btn-toggle { padding: 4px 10px; border: none; border-radius: 6px; font-size: 0.75rem; font-weight: 700; cursor: pointer; }
.btn-toggle.on { background: rgba(0,217,126,0.12); color: var(--green); }
.btn-toggle.off { background: var(--bg3); color: var(--text3); }
.btn-ghost { background: none; border: 1px solid var(--border); color: var(--text2); font-size: 0.78rem; border-radius: 6px; padding: 4px 8px; cursor: pointer; }
.btn-del { background: none; border: none; color: var(--text3); cursor: pointer; font-size: 0.8rem; padding: 4px 6px; border-radius: 4px; }
.btn-del:hover { color: var(--red); }
.empty-state { text-align: center; padding: 1.5rem; color: var(--text3); font-size: 0.85rem; }
.modal-backdrop { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 1rem; }
.modal { background: var(--bg2); border: 1px solid var(--border); border-radius: 16px; width: 100%; max-width: 480px; box-shadow: 0 24px 48px rgba(0,0,0,0.3); }
.modal-wide { max-width: 640px; }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border); }
.modal-header h3 { font-size: 1rem; font-weight: 700; color: var(--text); margin: 0; }
.modal-body { padding: 1.25rem 1.5rem; }
.modal-footer { padding: 1rem 1.5rem; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 8px; }
.btn-close { background: none; border: none; color: var(--text3); cursor: pointer; font-size: 1rem; }
.field { margin-bottom: 1rem; }
.field-label { display: block; font-size: 0.78rem; font-weight: 600; color: var(--text2); margin-bottom: 5px; }
.field-input { width: 100%; padding: 9px 12px; border: 1.5px solid var(--border2); border-radius: 8px; background: var(--bg); color: var(--text); font-size: 0.85rem; outline: none; box-sizing: border-box; }
.field-input:focus { border-color: var(--accent); }
.event-checks { display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; }
.ev-check { display: flex; align-items: center; gap: 6px; font-size: 0.82rem; color: var(--text2); cursor: pointer; }
.ev-check input { accent-color: var(--accent); }
.err-msg { background: rgba(255,79,106,0.1); border: 1px solid rgba(255,79,106,0.3); border-radius: 8px; padding: 8px 12px; font-size: 0.82rem; color: var(--red); margin-top: 0.5rem; }
.btn-primary { padding: 9px 18px; background: var(--accent); color: #fff; border: none; border-radius: 8px; font-size: 0.85rem; font-weight: 700; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-outline { padding: 7px 14px; background: transparent; border: 1px solid var(--border2); border-radius: 8px; color: var(--text2); font-size: 0.82rem; cursor: pointer; margin-top: 0.75rem; }
.secret-note { font-size: 0.85rem; color: var(--yellow); margin-bottom: 0.75rem; }
.secret-box { display: block; font-family: var(--font-mono); font-size: 0.8rem; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; word-break: break-all; color: var(--text2); }
.delivery-list { display: flex; flex-direction: column; gap: 4px; max-height: 320px; overflow-y: auto; }
.delivery-row { display: flex; align-items: center; gap: 10px; padding: 7px 10px; background: var(--bg); border-radius: 6px; font-size: 0.8rem; }
.d-status { padding: 2px 7px; border-radius: 4px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; }
.d-status.success { background: rgba(0,217,126,0.12); color: var(--green); }
.d-status.failed { background: rgba(255,79,106,0.12); color: var(--red); }
.d-status.pending { background: rgba(255,209,30,0.12); color: var(--yellow); }
.d-event { font-family: var(--font-mono); color: var(--text2); flex: 1; }
.d-code { font-family: var(--font-mono); color: var(--text3); }
.d-attempts { color: var(--text3); }
.d-date { color: var(--text3); white-space: nowrap; }
</style>
