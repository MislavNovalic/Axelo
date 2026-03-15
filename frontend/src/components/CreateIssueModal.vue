<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <h2>+ New Issue</h2>
      <IssueTemplateSelector :project-id="projectId" @apply="applyTemplate" />
      <div class="form-group">
        <label class="fd-label">Title *</label>
        <input v-model="form.title" class="fd-input" placeholder="What needs to be done?" />
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="fd-label">Type</label>
          <select v-model="form.type" class="fd-input">
            <option value="task">Task</option>
            <option value="bug">Bug</option>
            <option value="story">Story</option>
            <option value="epic">Epic</option>
          </select>
        </div>
        <div class="form-group">
          <label class="fd-label">Priority</label>
          <select v-model="form.priority" class="fd-input">
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
      </div>
      <div class="form-group">
        <label class="fd-label">Description</label>
        <textarea v-model="form.description" class="fd-input" style="height:88px;resize:none;" placeholder="Add more context..." />
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="fd-label">Story Points</label>
          <input v-model.number="form.story_points" type="number" min="0" class="fd-input" placeholder="0" />
        </div>
        <div v-if="sprints?.length" class="form-group">
          <label class="fd-label">Sprint</label>
          <select v-model="form.sprint_id" class="fd-input">
            <option :value="null">Backlog</option>
            <option v-for="s in sprints" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </div>
      </div>
      <div class="modal-actions">
        <button class="btn-ghost" @click="$emit('close')">Cancel</button>
        <button class="btn-primary" :disabled="!form.title.trim() || loading" @click="submit">
          {{ loading ? 'Creating...' : 'Create Issue' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import IssueTemplateSelector from '@/components/IssueTemplateSelector.vue'

import { ref } from 'vue'
import { useIssuesStore } from '@/store/issues'
const props = defineProps({ projectId: Number, sprints: Array, defaultSprintId: { type: Number, default: null } })
const emit = defineEmits(['close', 'created'])
const issuesStore = useIssuesStore()
const loading = ref(false)
const form = ref({ title: '', type: 'task', priority: 'medium', status: 'todo', description: '', story_points: null, sprint_id: props.defaultSprintId })

function applyTemplate(tpl) {
  if (!tpl) {
    form.value = { title: '', type: 'task', priority: 'medium', status: 'todo', description: '', story_points: null, sprint_id: props.defaultSprintId }
    return
  }
  if (tpl.type)        form.value.type        = tpl.type
  if (tpl.priority)    form.value.priority    = tpl.priority
  if (tpl.title)       form.value.title       = tpl.title
  if (tpl.description) form.value.description = tpl.description
}

async function submit() {
  if (!form.value.title.trim()) return
  loading.value = true
  try {
    const issue = await issuesStore.createIssue(props.projectId, form.value)
    emit('created', issue); emit('close')
  } finally { loading.value = false }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 200; padding: 1rem;
}
.modal {
  background: var(--bg2); border: 1px solid var(--border2); border-radius: 14px;
  padding: 1.75rem; width: 100%; max-width: 460px;
  box-shadow: 0 32px 64px rgba(0,0,0,0.6);
  animation: modalIn 0.2s ease;
}
@keyframes modalIn { from { opacity:0; transform:scale(0.96) translateY(8px); } to { opacity:1; transform:scale(1) translateY(0); } }
.modal h2 { font-family: var(--font-display); font-size: 1.15rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 1.25rem; }
.form-group { margin-bottom: 0.9rem; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 1.25rem; }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 640px) {
  .modal-overlay { padding: 0; align-items: flex-end; }
  .modal { max-width: 100%; border-radius: 14px 14px 0 0; min-height: auto; }
  .form-row { grid-template-columns: 1fr; }
}
</style>
