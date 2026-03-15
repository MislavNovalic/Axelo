<template>
  <div class="importer-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Import Issues</h1>
        <p class="page-sub">{{ project?.name }} · Import from Jira, Linear, CSV, or another Axelo project</p>
      </div>
    </div>

    <!-- Source picker -->
    <div class="source-grid">
      <div
        v-for="s in sources"
        :key="s.id"
        class="source-card"
        :class="{ selected: source === s.id }"
        @click="source = s.id"
      >
        <div class="source-icon">{{ s.icon }}</div>
        <div class="source-name">{{ s.name }}</div>
        <div class="source-desc">{{ s.desc }}</div>
      </div>
    </div>

    <!-- Upload + preview -->
    <div v-if="source" class="upload-section">
      <div class="upload-card" :class="{ dragover }"
        @dragover.prevent="dragover = true"
        @dragleave="dragover = false"
        @drop.prevent="onDrop"
      >
        <input ref="fileInput" type="file" :accept="acceptedTypes" class="file-input" @change="onFileChange" />
        <div v-if="!file" class="drop-hint" @click="$refs.fileInput.click()">
          <div class="drop-icon">📂</div>
          <div>Drop your <strong>{{ sourceName }}</strong> export here, or <span class="link">browse</span></div>
          <div class="drop-sub">{{ acceptHint }}</div>
        </div>
        <div v-else class="file-selected">
          <span class="file-icon">📄</span>
          <span class="file-name">{{ file.name }}</span>
          <span class="file-size">{{ fmtSize(file.size) }}</span>
          <button class="btn-remove" @click="clearFile">✕</button>
        </div>
      </div>

      <div class="action-row">
        <button class="btn-secondary" @click="preview" :disabled="!file || previewing">
          {{ previewing ? 'Validating…' : '👁 Preview' }}
        </button>
        <button class="btn-primary" @click="runImport" :disabled="!previewData || importing">
          {{ importing ? 'Importing…' : '⬆ Import' }}
        </button>
      </div>

      <!-- Preview panel -->
      <transition name="fade">
        <div v-if="previewData" class="preview-panel">
          <div class="preview-header">
            <h3 class="preview-title">Preview · {{ previewData.total.toLocaleString() }} issues found</h3>
          </div>

          <div class="stats-row">
            <div class="stat-block" v-for="(v, k) in previewData.type_distribution" :key="k">
              <span class="stat-val">{{ v }}</span>
              <span class="stat-label">{{ k }}</span>
            </div>
          </div>

          <div v-if="previewData.warnings?.length" class="warnings">
            <div v-for="w in previewData.warnings" :key="w" class="warning-row">⚠ {{ w }}</div>
          </div>

          <div class="sample-list">
            <div class="sample-header">Sample (first 5)</div>
            <div v-for="(s, i) in previewData.sample" :key="i" class="sample-row">
              <span class="sample-type">{{ typeIcon(s.type) }}</span>
              <span class="sample-title">{{ s.title }}</span>
              <span class="status-chip" :class="s.status">{{ s.status.replace('_', ' ') }}</span>
              <span class="pts" v-if="s.story_points">{{ s.story_points }}pt</span>
            </div>
          </div>
        </div>
      </transition>

      <!-- Error -->
      <transition name="fade">
        <div v-if="importError" class="error-banner">⚠ {{ importError }}</div>
      </transition>
    </div>

    <!-- Active jobs -->
    <div v-if="jobs.length" class="jobs-section">
      <h3 class="section-title">Import History</h3>
      <div class="job-list">
        <div v-for="job in jobs" :key="job.id" class="job-row">
          <span class="source-tag">{{ job.source }}</span>
          <div class="job-progress">
            <div class="progress-bar">
              <div class="progress-fill" :class="job.status" :style="{ width: job.progress_pct + '%' }"></div>
            </div>
            <span class="progress-pct">{{ job.progress_pct }}%</span>
          </div>
          <span class="job-counts">{{ job.imported }} imported · {{ job.skipped }} skipped</span>
          <span class="job-status" :class="job.status">{{ job.status }}</span>
          <span class="job-date">{{ fmtDate(job.created_at) }}</span>
          <button v-if="job.status === 'running' || job.status === 'pending'" class="btn-refresh" @click="pollJob(job)">↻</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi } from '@/api'
import api from '@/api'

const route = useRoute()
const projectId = parseInt(route.params.id)

const project    = ref(null)
const source     = ref('')
const file       = ref(null)
const dragover   = ref(false)
const previewing = ref(false)
const importing  = ref(false)
const previewData = ref(null)
const importError = ref('')
const jobs       = ref([])
const fileInput  = ref(null)

const sources = [
  { id: 'jira',   icon: '🔵', name: 'Jira',   desc: 'JSON export from Jira Cloud or Server' },
  { id: 'linear', icon: '🟣', name: 'Linear',  desc: 'JSON export from Linear workspace' },
  { id: 'csv',    icon: '📊', name: 'CSV',     desc: 'Generic CSV with title, status, type columns' },
  { id: 'axelo',  icon: '⚡', name: 'Axelo',   desc: 'Re-import from another Axelo project export' },
]

const sourceName = computed(() => sources.find(s => s.id === source.value)?.name || '')
const acceptedTypes = computed(() => source.value === 'csv' ? '.csv' : '.json')
const acceptHint = computed(() => source.value === 'csv'
  ? 'CSV file with columns: title, description, status, priority, type, story_points'
  : 'JSON export file — up to 10 MB')

function typeIcon(t) {
  return { bug: '🐛', story: '📖', task: '✅', epic: '⚡' }[t] ?? '•'
}
function fmtSize(bytes) {
  return bytes > 1024*1024 ? `${(bytes/1024/1024).toFixed(1)} MB` : `${Math.round(bytes/1024)} KB`
}
function fmtDate(iso) {
  return new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function onDrop(e) {
  dragover.value = false
  const f = e.dataTransfer.files[0]
  if (f) setFile(f)
}
function onFileChange(e) {
  const f = e.target.files[0]
  if (f) setFile(f)
}
function setFile(f) {
  file.value = f
  previewData.value = null
  importError.value = ''
}
function clearFile() {
  file.value = null
  previewData.value = null
  if (fileInput.value) fileInput.value.value = ''
}

async function preview() {
  previewing.value = true
  importError.value = ''
  previewData.value = null
  try {
    const form = new FormData()
    form.append('file', file.value)
    const res = await api.post(`/projects/${projectId}/import/preview?source=${source.value}`, form,
      { headers: { 'Content-Type': 'multipart/form-data' } })
    previewData.value = res.data
  } catch (e) {
    importError.value = e.response?.data?.detail || 'Failed to parse file'
  } finally { previewing.value = false }
}

async function runImport() {
  importing.value = true
  importError.value = ''
  try {
    const form = new FormData()
    form.append('file', file.value)
    const res = await api.post(`/projects/${projectId}/import/run?source=${source.value}`, form,
      { headers: { 'Content-Type': 'multipart/form-data' } })
    clearFile()
    previewData.value = null
    await fetchJobs()
    // Poll the new job
    const newJob = jobs.value.find(j => j.id === res.data.job_id)
    if (newJob) setTimeout(() => pollJob(newJob), 2000)
  } catch (e) {
    importError.value = e.response?.data?.detail || 'Import failed'
  } finally { importing.value = false }
}

async function fetchJobs() {
  const res = await api.get(`/projects/${projectId}/import/jobs`)
  jobs.value = res.data
}

async function pollJob(job) {
  const res = await api.get(`/projects/${projectId}/import/jobs/${job.id}`)
  const idx = jobs.value.findIndex(j => j.id === job.id)
  if (idx >= 0) jobs.value[idx] = res.data
  if (res.data.status === 'running' || res.data.status === 'pending') {
    setTimeout(() => pollJob(res.data), 2000)
  }
}

onMounted(async () => {
  try {
    const [projRes] = await Promise.all([projectsApi.get(projectId), fetchJobs()])
    project.value = projRes.data
  } catch (e) {
    if (e.response?.status === 403) {
      importError.value = 'You need Admin or Owner role to access the importer.'
    }
  }
})
</script>

<style scoped>
.importer-page { padding: 2rem; max-width: 800px; margin: 0 auto; }
.page-header { margin-bottom: 1.5rem; }
.page-title { font-family: var(--font-display); font-size: 1.6rem; font-weight: 800; color: var(--text); margin-bottom: 0.2rem; }
.page-sub { font-size: 0.85rem; color: var(--text2); }
.source-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 1.5rem; }
.source-card { background: var(--bg2); border: 1.5px solid var(--border); border-radius: 12px; padding: 1rem; text-align: center; cursor: pointer; transition: border-color 0.2s, background 0.2s; }
.source-card.selected { border-color: var(--accent); background: rgba(16,185,129,0.07); }
.source-card:hover:not(.selected) { border-color: var(--border2); }
.source-icon { font-size: 1.5rem; margin-bottom: 6px; }
.source-name { font-size: 0.85rem; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.source-desc { font-size: 0.72rem; color: var(--text3); line-height: 1.4; }
.upload-section { display: flex; flex-direction: column; gap: 1rem; }
.upload-card { border: 2px dashed var(--border2); border-radius: 14px; padding: 2rem; transition: border-color 0.2s, background 0.2s; position: relative; }
.upload-card.dragover { border-color: var(--accent); background: rgba(16,185,129,0.05); }
.file-input { position: absolute; inset: 0; opacity: 0; pointer-events: none; }
.drop-hint { text-align: center; cursor: pointer; }
.drop-icon { font-size: 2rem; margin-bottom: 8px; }
.drop-hint div { font-size: 0.88rem; color: var(--text2); }
.link { color: var(--accent2); text-decoration: underline; cursor: pointer; }
.drop-sub { font-size: 0.75rem; color: var(--text3); margin-top: 4px; }
.file-selected { display: flex; align-items: center; gap: 10px; }
.file-icon { font-size: 1.2rem; }
.file-name { flex: 1; font-size: 0.85rem; color: var(--text); font-family: var(--font-mono); }
.file-size { font-size: 0.75rem; color: var(--text3); }
.btn-remove { background: none; border: none; color: var(--text3); cursor: pointer; font-size: 0.85rem; }
.action-row { display: flex; gap: 10px; }
.btn-primary { padding: 10px 20px; background: var(--accent); color: #fff; border: none; border-radius: 9px; font-size: 0.88rem; font-weight: 700; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { padding: 10px 20px; background: var(--bg2); border: 1.5px solid var(--border2); color: var(--text); border-radius: 9px; font-size: 0.88rem; font-weight: 600; cursor: pointer; }
.btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }
.preview-panel { background: var(--bg2); border: 1px solid var(--border); border-radius: 14px; padding: 1.25rem 1.5rem; }
.preview-header { margin-bottom: 1rem; }
.preview-title { font-size: 0.95rem; font-weight: 700; color: var(--text); margin: 0; }
.stats-row { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 1rem; }
.stat-block { background: var(--bg3); border-radius: 8px; padding: 8px 12px; text-align: center; }
.stat-val { display: block; font-family: var(--font-display); font-size: 1.1rem; font-weight: 700; color: var(--text); }
.stat-label { font-size: 0.72rem; color: var(--text3); text-transform: capitalize; }
.warnings { margin-bottom: 0.75rem; }
.warning-row { background: rgba(255,209,30,0.08); border: 1px solid rgba(255,209,30,0.25); border-radius: 7px; padding: 7px 11px; font-size: 0.8rem; color: var(--yellow); margin-bottom: 4px; }
.sample-list { border-top: 1px solid var(--border); padding-top: 0.75rem; }
.sample-header { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text3); margin-bottom: 6px; }
.sample-row { display: flex; align-items: center; gap: 8px; padding: 7px 0; border-bottom: 1px solid var(--border); font-size: 0.82rem; }
.sample-row:last-child { border-bottom: none; }
.sample-type { flex-shrink: 0; }
.sample-title { flex: 1; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.status-chip { padding: 2px 7px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; text-transform: capitalize; background: var(--bg3); color: var(--text3); }
.status-chip.done { background: rgba(0,217,126,0.1); color: var(--green); }
.status-chip.in_progress { background: rgba(16,185,129,0.1); color: var(--accent2); }
.pts { font-family: var(--font-mono); font-size: 0.72rem; color: var(--text3); }
.error-banner { background: rgba(255,79,106,0.1); border: 1px solid rgba(255,79,106,0.3); border-radius: 10px; padding: 12px 16px; font-size: 0.85rem; color: var(--red); }
.jobs-section { margin-top: 2rem; }
.section-title { font-size: 0.9rem; font-weight: 700; color: var(--text); margin-bottom: 0.75rem; }
.job-list { display: flex; flex-direction: column; gap: 6px; }
.job-row { display: flex; align-items: center; gap: 10px; padding: 10px 12px; background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; font-size: 0.8rem; }
.source-tag { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; padding: 2px 7px; background: rgba(16,185,129,0.1); color: var(--accent2); border-radius: 4px; flex-shrink: 0; }
.job-progress { display: flex; align-items: center; gap: 6px; flex: 1; min-width: 80px; }
.progress-bar { flex: 1; height: 6px; background: var(--bg3); border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 3px; transition: width 0.4s; }
.progress-fill.done { background: var(--green); }
.progress-fill.running { background: var(--accent2); animation: pulse 1.5s ease-in-out infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.6} }
.progress-fill.pending { background: var(--text3); }
.progress-fill.failed { background: var(--red); }
.progress-pct { font-family: var(--font-mono); font-size: 0.72rem; color: var(--text3); flex-shrink: 0; }
.job-counts { color: var(--text3); flex-shrink: 0; }
.job-status { padding: 2px 7px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; text-transform: capitalize; flex-shrink: 0; }
.job-status.done { background: rgba(0,217,126,0.1); color: var(--green); }
.job-status.running { background: rgba(16,185,129,0.1); color: var(--accent2); }
.job-status.pending { background: var(--bg3); color: var(--text3); }
.job-status.failed { background: rgba(255,79,106,0.1); color: var(--red); }
.job-date { color: var(--text3); white-space: nowrap; }
.btn-refresh { background: none; border: none; color: var(--accent2); cursor: pointer; font-size: 0.9rem; padding: 2px 6px; }
.fade-enter-active { transition: opacity 0.3s, transform 0.3s; }
.fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from { opacity: 0; transform: translateY(-6px); }
.fade-leave-to { opacity: 0; }
</style>
