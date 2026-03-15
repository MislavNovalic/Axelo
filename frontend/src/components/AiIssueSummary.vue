<template>
  <div class="ai-summary-panel">
    <div class="panel-header">
      <div class="ai-badge">
        <span class="spark">✦</span> AI Summary
      </div>
      <button
        class="btn-summarise"
        @click="generate"
        :disabled="loading || !aiAvailable"
        :title="!aiAvailable ? 'AI not configured on this instance' : ''"
      >
        <span v-if="!loading">{{ summary ? 'Regenerate' : 'Summarise thread' }}</span>
        <span v-else class="btn-loader"><span></span><span></span><span></span></span>
      </button>
    </div>

    <transition name="ai-fade">
      <div v-if="summary" class="summary-body">
        <p class="summary-text">{{ summary }}</p>

        <div v-if="actions.length" class="actions-section">
          <div class="actions-label">Suggested next actions</div>
          <ul class="actions-list">
            <li v-for="(a, i) in actions" :key="i" class="action-item">
              <span class="action-dot">→</span> {{ a }}
            </li>
          </ul>
        </div>

        <div class="meta-row">
          <span class="model-badge">{{ model }}</span>
          <span class="tokens-badge">{{ tokensUsed.toLocaleString() }} tokens</span>
          <button class="btn-ghost-xs" @click="dismiss">✕ Dismiss</button>
        </div>
      </div>
    </transition>

    <transition name="ai-fade">
      <div v-if="error" class="error-msg">⚠ {{ error }}</div>
    </transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api'

const props = defineProps({
  projectId: { type: Number, required: true },
  issueId:   { type: Number, required: true },
  aiAvailable: { type: Boolean, default: true },
})

const loading   = ref(false)
const summary   = ref('')
const actions   = ref([])
const model     = ref('')
const tokensUsed = ref(0)
const error     = ref('')

async function generate() {
  loading.value = true
  error.value   = ''
  try {
    const res = await api.post(
      `/projects/${props.projectId}/issues/${props.issueId}/ai/summarise`
    )
    summary.value   = res.data.summary
    actions.value   = res.data.suggested_actions || []
    model.value     = res.data.model || ''
    tokensUsed.value = res.data.tokens_used || 0
  } catch (e) {
    error.value = e.response?.data?.detail || 'Failed to generate summary. Try again.'
  } finally {
    loading.value = false
  }
}

function dismiss() {
  summary.value = ''
  actions.value = []
  error.value   = ''
}
</script>

<style scoped>
.ai-summary-panel {
  border: 1px solid rgba(6, 182, 212, 0.25);
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(6,182,212,0.04) 0%, rgba(16,185,129,0.04) 100%);
  padding: 1rem 1.25rem;
  margin-top: 1.5rem;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.ai-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.78rem;
  font-weight: 700;
  color: #06b6d4;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.spark {
  font-size: 0.9rem;
  animation: sparkle 2s ease-in-out infinite;
}
@keyframes sparkle {
  0%,100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.3); }
}
.btn-summarise {
  padding: 6px 14px;
  background: rgba(6, 182, 212, 0.12);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 8px;
  color: #06b6d4;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
  min-height: 32px;
  display: flex;
  align-items: center;
}
.btn-summarise:hover:not(:disabled) {
  background: rgba(6, 182, 212, 0.2);
  border-color: rgba(6, 182, 212, 0.5);
}
.btn-summarise:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.btn-loader {
  display: flex;
  gap: 4px;
  align-items: center;
}
.btn-loader span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #06b6d4;
  animation: bounce 0.8s ease-in-out infinite;
}
.btn-loader span:nth-child(2) { animation-delay: 0.15s; }
.btn-loader span:nth-child(3) { animation-delay: 0.3s; }
@keyframes bounce {
  0%,60%,100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}
.summary-body {
  margin-top: 1rem;
  border-top: 1px solid rgba(6,182,212,0.15);
  padding-top: 0.875rem;
}
.summary-text {
  font-size: 0.88rem;
  color: var(--text);
  line-height: 1.65;
  margin-bottom: 0.875rem;
}
.actions-section {
  margin-bottom: 0.875rem;
}
.actions-label {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text3);
  margin-bottom: 0.4rem;
}
.actions-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.action-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 0.83rem;
  color: var(--text2);
  line-height: 1.5;
}
.action-dot {
  color: #06b6d4;
  flex-shrink: 0;
  margin-top: 1px;
}
.meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 0.5rem;
}
.model-badge, .tokens-badge {
  font-size: 0.68rem;
  padding: 2px 7px;
  border-radius: 4px;
  font-family: var(--font-mono);
  background: rgba(6,182,212,0.08);
  color: var(--text3);
  border: 1px solid rgba(6,182,212,0.15);
}
.btn-ghost-xs {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--text3);
  font-size: 0.72rem;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: color 0.15s;
}
.btn-ghost-xs:hover { color: var(--text2); }
.error-msg {
  margin-top: 0.75rem;
  padding: 8px 12px;
  background: rgba(255,79,106,0.1);
  border: 1px solid rgba(255,79,106,0.3);
  border-radius: 8px;
  font-size: 0.82rem;
  color: var(--red);
}
.ai-fade-enter-active { transition: opacity 0.3s, transform 0.3s; }
.ai-fade-leave-active { transition: opacity 0.2s; }
.ai-fade-enter-from { opacity: 0; transform: translateY(-6px); }
.ai-fade-leave-to { opacity: 0; }
</style>
