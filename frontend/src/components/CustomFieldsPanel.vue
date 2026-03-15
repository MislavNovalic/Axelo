<template>
  <div v-if="fields.length" class="cf-panel">
    <div class="cf-header">
      <span class="cf-title">Custom Fields</span>
    </div>
    <div class="cf-rows">
      <div v-for="item in fieldValues" :key="item.field.id" class="cf-row">
        <label class="cf-label">
          {{ item.field.name }}
          <span v-if="item.field.required" class="required">*</span>
        </label>
        <!-- Text -->
        <input v-if="item.field.field_type === 'text'"
          v-model="item.value" class="cf-input" type="text"
          :placeholder="item.field.name" @change="save" />
        <!-- Number -->
        <input v-else-if="item.field.field_type === 'number'"
          v-model.number="item.value" class="cf-input cf-short" type="number"
          @change="save" />
        <!-- Date -->
        <input v-else-if="item.field.field_type === 'date'"
          v-model="item.value" class="cf-input cf-short" type="date"
          @change="save" />
        <!-- Boolean -->
        <label v-else-if="item.field.field_type === 'boolean'" class="cf-toggle">
          <input type="checkbox" v-model="item.value" @change="save" />
          <span class="toggle-track"></span>
        </label>
        <!-- Select -->
        <select v-else-if="item.field.field_type === 'select'"
          v-model="item.value" class="cf-select" @change="save">
          <option value="">— none —</option>
          <option v-for="opt in item.field.options" :key="opt" :value="opt">{{ opt }}</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { customFieldsApi } from '@/api'

const props = defineProps({ projectId: Number, issueId: Number })
const fields = ref([])
const fieldValues = ref([])

onMounted(fetch)

async function fetch() {
  if (!props.projectId || !props.issueId) return
  try {
    const r = await customFieldsApi.getIssueFields(props.projectId, props.issueId)
    fields.value = r.data.map(x => x.field)
    fieldValues.value = r.data.map(x => ({ field: x.field, value: x.value ?? '' }))
  } catch { /* no custom fields */ }
}

async function save() {
  const payload = fieldValues.value.map(x => ({ field_id: x.field.id, value: x.value }))
  await customFieldsApi.setIssueFields(props.projectId, props.issueId, payload)
}
</script>

<style scoped>
.cf-panel { margin-top: 1.5rem; }
.cf-header { margin-bottom: 0.75rem; }
.cf-title { font-size: 0.82rem; font-weight: 600; color: var(--text); }
.cf-rows { display: flex; flex-direction: column; gap: 0.75rem; }
.cf-row { display: flex; align-items: center; gap: 12px; }
.cf-label {
  font-size: 0.78rem; color: var(--text3); min-width: 110px; flex-shrink: 0;
}
.required { color: var(--red); margin-left: 2px; }
.cf-input {
  flex: 1; background: var(--bg3); border: 1px solid var(--border2);
  border-radius: 6px; padding: 5px 9px; font-size: 0.82rem; color: var(--text);
  font-family: var(--font-body); outline: none; transition: border 0.15s;
}
.cf-input:focus { border-color: var(--accent); }
.cf-short { flex: none; width: 120px; }
.cf-select {
  flex: 1; background: var(--bg3); border: 1px solid var(--border2);
  border-radius: 6px; padding: 5px 9px; font-size: 0.82rem; color: var(--text);
  font-family: var(--font-body); outline: none; cursor: pointer;
}
/* Toggle */
.cf-toggle { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.cf-toggle input { position: absolute; opacity: 0; pointer-events: none; }
.toggle-track {
  width: 32px; height: 17px; border-radius: 9px; background: var(--bg3);
  border: 1px solid var(--border2); position: relative; transition: background 0.2s;
}
.cf-toggle input:checked ~ .toggle-track { background: var(--accent); border-color: var(--accent); }
.toggle-track::after {
  content: ''; position: absolute; top: 1px; left: 2px;
  width: 13px; height: 13px; border-radius: 50%; background: var(--text3);
  transition: transform 0.2s, background 0.2s;
}
.cf-toggle input:checked ~ .toggle-track::after {
  transform: translateX(14px); background: #fff;
}
</style>
