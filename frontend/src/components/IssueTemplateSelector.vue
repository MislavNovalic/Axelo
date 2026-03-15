<template>
  <div v-if="templates.length" class="template-bar">
    <span class="template-label">📋 Start from template:</span>
    <div class="template-chips">
      <button
        v-for="t in templates"
        :key="t.id"
        class="template-chip"
        :class="{ active: selected === t.id }"
        @click="select(t)"
        :title="t.description"
      >
        <span class="chip-dot" :class="`type-${t.type}`"></span>
        {{ t.name }}
      </button>
      <button v-if="selected" class="template-clear" @click="clear">✕ Clear</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { templatesApi } from '@/api'

const props = defineProps({ projectId: Number })
const emit  = defineEmits(['apply'])

const templates = ref([])
const selected  = ref(null)

onMounted(async () => {
  if (!props.projectId) return
  try {
    const r = await templatesApi.list(props.projectId)
    templates.value = r.data
  } catch { /* project has no templates */ }
})

function select(t) {
  selected.value = t.id
  emit('apply', {
    type:        t.type,
    priority:    t.priority,
    title:       t.title_template || '',
    description: t.body_template  || '',
  })
}

function clear() {
  selected.value = null
  emit('apply', null)
}
</script>

<style scoped>
.template-bar {
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 0.75rem;
}
.template-label { font-size: 0.72rem; color: var(--text3); display: block; margin-bottom: 0.4rem; }
.template-chips { display: flex; flex-wrap: wrap; gap: 5px; }
.template-chip {
  display: flex; align-items: center; gap: 5px;
  background: var(--bg3); border: 1px solid var(--border2);
  padding: 4px 10px; border-radius: 6px;
  font-size: 0.76rem; color: var(--text2); cursor: pointer;
  font-family: var(--font-body); transition: all 0.12s;
}
.template-chip:hover  { border-color: var(--accent); color: var(--text); }
.template-chip.active { border-color: var(--accent); background: rgba(16,185,129,0.1); color: var(--accent2); }
.chip-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.type-bug   { background: var(--red); }
.type-story { background: var(--green); }
.type-task  { background: var(--accent2); }
.type-epic  { background: #06b6d4; }
.template-clear {
  background: none; border: none; cursor: pointer;
  font-size: 0.72rem; color: var(--text3); padding: 4px 6px;
}
.template-clear:hover { color: var(--red); }
</style>
