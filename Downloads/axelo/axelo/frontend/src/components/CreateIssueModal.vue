<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <h2>+ New Issue</h2>

      <!-- Template picker -->
      <div v-if="templates.length" class="form-group">
        <label class="fd-label">Start from template</label>
        <div class="template-row">
          <button
            v-for="t in templates"
            :key="t.id"
            class="template-chip"
            :class="{ active: selectedTemplate?.id === t.id }"
            @click="applyTemplate(t)"
          >{{ t.name }}</button>
          <button v-if="selectedTemplate" class="template-chip clear" @click="clearTemplate">✕ Clear</button>
        </div>
      </div>

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
import { ref, onMounted } from 'vue'
import { useIssuesStore } from '@/store/issues'
import { templatesApi } from '@/api'

const props = defineProps({ projectId: Number, sprints: Array })
const emit = defineEmits(['close', 'created'])
const issuesStore = useIssuesStore()
const loading = ref(false)
const templates = ref([])
const selectedTemplate = ref(null)

const defaultForm = () => ({ title: '', type: 'task', priority: 'medium', description: '', story_points: null, sprint_id: null })
const form = ref(defaultForm())

onMounted(async () => {
  try {
    const res = await templatesApi.list(props.projectId)
    templates.value = res.data
  } catch {
    // templates are optional — ignore errors
  }
})

function applyTemplate(t) {
  selectedTemplate.value = t
  form.value = {
    ...form.value,
    type: t.type,
    priority: t.priority,
    description: t.description || '',
    story_points: t.story_points || null,
  }
}

function clearTemplate() {
  selectedTemplate.value = null
  form.value = defaultForm()
}

async function submit() {
  if (!form.value.title.trim()) return
  loading.value = true
  try {
    const issue = await issuesStore.createIssue(props.projectId, form.value)
    emit('created', issue)
    emit('close')
  } finally {
    loading.value = false
  }
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

.template-row { display: flex; flex-wrap: wrap; gap: 6px; }
.template-chip {
  font-size: 0.72rem; padding: 3px 10px; border-radius: 20px; cursor: pointer;
  border: 1px solid var(--border2); background: var(--bg3); color: var(--text2);
  transition: all 0.15s;
}
.template-chip:hover { border-color: var(--accent); color: var(--accent2); }
.template-chip.active { border-color: var(--accent); background: rgba(92,79,255,0.12); color: var(--accent2); }
.template-chip.clear { border-color: transparent; color: var(--text3); }
.template-chip.clear:hover { color: var(--red); }
</style>
