<template>
  <div class="attachments-wrap">
    <div class="attach-header">
      <span class="attach-title">📎 Attachments</span>
      <span class="attach-count" v-if="files.length">{{ files.length }}</span>
    </div>

    <!-- Upload zone -->
    <div
      class="drop-zone"
      :class="{ dragging }"
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="onDrop"
      @click="fileInput.click()"
    >
      <input ref="fileInput" type="file" multiple class="hidden-input" @change="onFileChange" />
      <div v-if="uploading" class="upload-progress">
        <div class="upload-spinner"></div>
        <span>Uploading…</span>
      </div>
      <div v-else class="drop-hint">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        <span>Drop files or click to attach</span>
        <span class="drop-sub">Max 50 MB · Images, PDFs, docs, videos</span>
      </div>
    </div>

    <div v-if="uploadError" class="upload-error">{{ uploadError }}</div>

    <!-- File list -->
    <div v-if="files.length" class="file-list">
      <a
        v-for="f in files" :key="f.id"
        :href="downloadUrl(f)"
        target="_blank"
        class="file-row"
      >
        <span class="file-icon">{{ fileIcon(f.content_type) }}</span>
        <div class="file-info">
          <span class="file-name">{{ f.filename }}</span>
          <span class="file-meta">{{ formatSize(f.size_bytes) }} · {{ timeAgo(f.created_at) }} · {{ f.uploader?.full_name }}</span>
        </div>
        <button class="file-delete" @click.prevent="deleteFile(f)" title="Delete">✕</button>
      </a>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import { filesApi } from '@/api'

const props = defineProps({ projectId: Number, issueId: Number })
const files       = ref([])
const dragging    = ref(false)
const uploading   = ref(false)
const uploadError = ref('')
const fileInput   = ref(null)

const token = () => localStorage.getItem('token')

onMounted(fetchFiles)
async function fetchFiles() {
  try {
    const r = await filesApi.list(props.projectId, props.issueId)
    files.value = r.data
  } catch { /* silent */ }
}

function onDrop(e) {
  dragging.value = false
  const f = Array.from(e.dataTransfer.files)
  if (f.length) uploadFiles(f)
}
function onFileChange(e) { uploadFiles(Array.from(e.target.files)) }

async function uploadFiles(selected) {
  uploadError.value = ''
  for (const file of selected) {
    if (file.size > 50 * 1024 * 1024) {
      uploadError.value = `${file.name} exceeds 50 MB`
      continue
    }
    uploading.value = true
    try {
      const fd = new FormData()
      fd.append('file', file)
      const r = await filesApi.upload(props.projectId, props.issueId, fd)
      files.value.push(r.data)
    } catch (e) {
      uploadError.value = e.response?.data?.detail || 'Upload failed'
    } finally { uploading.value = false }
  }
}

async function deleteFile(f) {
  if (!confirm(`Delete "${f.filename}"?`)) return
  await filesApi.delete(props.projectId, props.issueId, f.id)
  files.value = files.value.filter(x => x.id !== f.id)
}

function downloadUrl(f) {
  return `/api/projects/${props.projectId}/issues/${props.issueId}/attachments/${f.id}/download`
}

function fileIcon(mime) {
  if (!mime) return '📄'
  if (mime.startsWith('image/')) return '🖼'
  if (mime === 'application/pdf') return '📕'
  if (mime.startsWith('video/')) return '🎬'
  if (mime.includes('spreadsheet') || mime.includes('csv')) return '📊'
  if (mime.includes('word') || mime.includes('document')) return '📝'
  if (mime.includes('zip')) return '🗜'
  return '📄'
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const u = ['B','KB','MB','GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${u[i]}`
}

function timeAgo(iso) {
  try { return formatDistanceToNow(new Date(iso), { addSuffix: true }) } catch { return '' }
}
</script>

<style scoped>
.attachments-wrap { margin-top: 1.5rem; }
.attach-header { display: flex; align-items: center; gap: 6px; margin-bottom: 0.6rem; }
.attach-title { font-size: 0.82rem; font-weight: 600; color: var(--text); }
.attach-count {
  background: var(--bg3); color: var(--text3);
  font-size: 0.65rem; font-weight: 700; padding: 1px 6px; border-radius: 8px;
}

.drop-zone {
  border: 1.5px dashed var(--border2); border-radius: 10px;
  padding: 1.25rem; cursor: pointer; transition: all 0.2s;
  text-align: center;
}
.drop-zone:hover, .drop-zone.dragging {
  border-color: var(--accent); background: rgba(16,185,129,0.05);
}
.hidden-input { display: none; }
.drop-hint { display: flex; flex-direction: column; align-items: center; gap: 5px; color: var(--text2); }
.drop-hint svg { color: var(--text3); }
.drop-hint span { font-size: 0.82rem; }
.drop-sub { font-size: 0.7rem; color: var(--text3); }

.upload-progress { display: flex; align-items: center; gap: 8px; color: var(--text2); font-size: 0.82rem; }
.upload-spinner {
  width: 18px; height: 18px; border-radius: 50%;
  border: 2px solid var(--border2); border-top-color: var(--accent);
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.upload-error { font-size: 0.75rem; color: var(--red); margin-top: 6px; }

.file-list { display: flex; flex-direction: column; gap: 3px; margin-top: 8px; }
.file-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: 8px;
  background: var(--bg3); text-decoration: none;
  transition: background 0.12s;
}
.file-row:hover { background: rgba(16,185,129,0.08); }
.file-icon { font-size: 1.1rem; flex-shrink: 0; }
.file-info { flex: 1; min-width: 0; }
.file-name { display: block; font-size: 0.8rem; font-weight: 500; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.file-meta { font-size: 0.7rem; color: var(--text3); }
.file-delete {
  background: none; border: none; cursor: pointer; color: var(--text3);
  padding: 2px 4px; border-radius: 4px; font-size: 0.75rem;
  opacity: 0; transition: opacity 0.15s, color 0.15s;
}
.file-row:hover .file-delete { opacity: 1; }
.file-delete:hover { color: var(--red); }
</style>
