import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Only redirect to login on 401 for non-auth endpoints
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const isAuthEndpoint = err.config?.url?.startsWith('/auth/')
    if (err.response?.status === 401 && !isAuthEndpoint) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Auth — see Phase 3 section below for updated authApi

// Projects
export const projectsApi = {
  list: () => api.get('/projects/'),
  create: (data) => api.post('/projects/', data),
  get: (id) => api.get(`/projects/${id}`),
  update: (id, data) => api.patch(`/projects/${id}`, data),
  delete: (id) => api.delete(`/projects/${id}`),
  addMember: (id, data) => api.post(`/projects/${id}/members`, data),
  updateMemberRole: (id, userId, data) => api.patch(`/projects/${id}/members/${userId}`, data),
  removeMember: (id, userId) => api.delete(`/projects/${id}/members/${userId}`),
}

// Issues
export const issuesApi = {
  list: (projectId, params) => api.get(`/projects/${projectId}/issues/`, { params }),
  create: (projectId, data) => api.post(`/projects/${projectId}/issues/`, data),
  get: (projectId, issueId) => api.get(`/projects/${projectId}/issues/${issueId}`),
  update: (projectId, issueId, data) => api.patch(`/projects/${projectId}/issues/${issueId}`, data),
  delete: (projectId, issueId) => api.delete(`/projects/${projectId}/issues/${issueId}`),
  addComment: (projectId, issueId, data) => api.post(`/projects/${projectId}/issues/${issueId}/comments`, data),
}

// Sprints
export const sprintsApi = {
  list: (projectId) => api.get(`/projects/${projectId}/sprints/`),
  create: (projectId, data) => api.post(`/projects/${projectId}/sprints/`, data),
  update: (projectId, sprintId, data) => api.patch(`/projects/${projectId}/sprints/${sprintId}`, data),
  delete: (projectId, sprintId) => api.delete(`/projects/${projectId}/sprints/${sprintId}`),
}

// ── Phase 4 ────────────────────────────────────────────────────────────────

// AI
export const aiApi = {
  summarise:  (pid, iid) => api.post(`/projects/${pid}/issues/${iid}/ai/summarise`),
  sprintPlan: (pid, data) => api.post(`/projects/${pid}/ai/sprint-plan`, data),
  usage:      (pid)       => api.get(`/projects/${pid}/ai/usage`),
}

// Organisations
export const orgsApi = {
  list:          ()                    => api.get('/orgs/'),
  create:        (data)                => api.post('/orgs/', data),
  get:           (slug)                => api.get(`/orgs/${slug}`),
  update:        (slug, data)          => api.patch(`/orgs/${slug}`, data),
  delete:        (slug)                => api.delete(`/orgs/${slug}`),
  listMembers:   (slug)                => api.get(`/orgs/${slug}/members`),
  inviteMember:  (slug, data)          => api.post(`/orgs/${slug}/members`, data),
  updateMember:  (slug, uid, data)     => api.patch(`/orgs/${slug}/members/${uid}`, data),
  removeMember:  (slug, uid)           => api.delete(`/orgs/${slug}/members/${uid}`),
  listProjects:  (slug)                => api.get(`/orgs/${slug}/projects`),
  attachProject: (slug, pid)           => api.post(`/orgs/${slug}/projects/${pid}`),
  detachProject: (slug, pid)           => api.delete(`/orgs/${slug}/projects/${pid}`),
  search:        (slug, q)             => api.get(`/orgs/${slug}/search`, { params: { q } }),
}

// Importer
export const importApi = {
  preview:   (pid, source, file) => {
    const form = new FormData(); form.append('file', file)
    return api.post(`/projects/${pid}/import/preview?source=${source}`, form)
  },
  run:       (pid, source, file) => {
    const form = new FormData(); form.append('file', file)
    return api.post(`/projects/${pid}/import/run?source=${source}`, form)
  },
  listJobs:  (pid)         => api.get(`/projects/${pid}/import/jobs`),
  getJob:    (pid, jobId)  => api.get(`/projects/${pid}/import/jobs/${jobId}`),
}

export default api

// Calendar
export const calendarApi = {
  getMonth: (year, month) => api.get('/calendar/', { params: { year, month } }),
  setDueDate: (issueId, due_date) => api.patch(`/calendar/${issueId}/due-date`, { due_date }),
}

export const statsApi = {
  dashboard: () => api.get('/stats/dashboard'),
}

// Notifications
export const notificationsApi = {
  list:       (limit = 40) => api.get(`/notifications?limit=${limit}`),
  markRead:   (id)         => api.patch(`/notifications/${id}/read`),
  markAllRead: ()          => api.post('/notifications/read-all'),
  unreadCount: ()          => api.get('/notifications/unread-count'),
}

// Search
export const searchApi = {
  query: (q) => api.get(`/search/?q=${encodeURIComponent(q)}`),
}

// Reports
export const reportsApi = {
  burndown:  (projectId, sprintId) => api.get(`/projects/${projectId}/reports/burndown?sprint_id=${sprintId}`),
  velocity:  (projectId)           => api.get(`/projects/${projectId}/reports/velocity`),
  cycleTime: (projectId)           => api.get(`/projects/${projectId}/reports/cycle-time`),
  issueFlow: (projectId, days=30)  => api.get(`/projects/${projectId}/reports/issue-flow?days=${days}`),
  auditLog:  (projectId, skip=0)   => api.get(`/projects/${projectId}/reports/audit-log?skip=${skip}&limit=50`),
}

// File attachments
export const filesApi = {
  list:     (projectId, issueId)             => api.get(`/projects/${projectId}/issues/${issueId}/attachments/`),
  upload:   (projectId, issueId, formData)   => api.post(`/projects/${projectId}/issues/${issueId}/attachments/`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  download: (projectId, issueId, attachId)   => `${api.defaults.baseURL}/projects/${projectId}/issues/${issueId}/attachments/${attachId}/download`,
  delete:   (projectId, issueId, attachId)   => api.delete(`/projects/${projectId}/issues/${issueId}/attachments/${attachId}`),
}

// Issue Templates
export const templatesApi = {
  list:    (projectId)          => api.get(`/projects/${projectId}/templates/`),
  create:  (projectId, data)    => api.post(`/projects/${projectId}/templates/`, data),
  update:  (projectId, id, d)   => api.patch(`/projects/${projectId}/templates/${id}`, d),
  delete:  (projectId, id)      => api.delete(`/projects/${projectId}/templates/${id}`),
}

// Custom Fields
export const customFieldsApi = {
  listFields:   (projectId)          => api.get(`/projects/${projectId}/fields/`),
  createField:  (projectId, data)    => api.post(`/projects/${projectId}/fields/`, data),
  updateField:  (projectId, id, d)   => api.patch(`/projects/${projectId}/fields/${id}`, d),
  deleteField:  (projectId, id)      => api.delete(`/projects/${projectId}/fields/${id}`),
  getIssueFields: (pid, iid)         => api.get(`/projects/${pid}/issues/${iid}/fields/`),
  setIssueFields: (pid, iid, vals)   => api.put(`/projects/${pid}/issues/${iid}/fields/`, vals),
}

// GitHub Integration
export const githubApi = {
  get:       (projectId)       => api.get(`/projects/${projectId}/github/`),
  connect:   (projectId, data) => api.post(`/projects/${projectId}/github/connect`, data),
  disconnect:(projectId)       => api.delete(`/projects/${projectId}/github/`),
}

// ── Phase 3 ────────────────────────────────────────────────────────────────

// Updated auth API — JSON login + 2FA
export const authApi = {
  register:          (data)              => api.post('/auth/register', data),
  login:             (email, password)   => api.post('/auth/login', { email, password }),
  verifyEmail:       (token)             => api.get(`/auth/verify-email?token=${token}`),
  resendVerification:(email)             => api.post('/auth/resend-verification', { email }),
  captchaConfig:     ()                  => api.get('/auth/captcha-config'),
  verify2fa: (temp_token, code) => api.post('/auth/2fa/verify', { temp_token, code }),
  tfa_setup:   ()              => api.post('/auth/2fa/setup'),
  tfa_enable:  (secret, code)  => api.post('/auth/2fa/enable', { secret, code }),
  tfa_disable: (code)          => api.post('/auth/2fa/disable', { code }),
  tfa_status:  ()              => api.get('/auth/2fa/status'),
  me:          ()              => api.get('/auth/me'),
  oauthUrl:    (provider)      => `/api/auth/oauth/${provider}`,
}

// Time tracking
export const timeApi = {
  list:   (pid, iid)      => api.get(`/projects/${pid}/issues/${iid}/time-logs`),
  log:    (pid, iid, data) => api.post(`/projects/${pid}/issues/${iid}/time-logs`, data),
  delete: (pid, iid, lid) => api.delete(`/projects/${pid}/issues/${iid}/time-logs/${lid}`),
  report: (pid)           => api.get(`/projects/${pid}/reports/time`),
}

// Outbound webhooks
export const webhooksApi = {
  list:           (pid)             => api.get(`/projects/${pid}/webhooks`),
  create:         (pid, data)       => api.post(`/projects/${pid}/webhooks`, data),
  update:         (pid, id, data)   => api.patch(`/projects/${pid}/webhooks/${id}`, data),
  delete:         (pid, id)         => api.delete(`/projects/${pid}/webhooks/${id}`),
  deliveries:     (pid, id)         => api.get(`/projects/${pid}/webhooks/${id}/deliveries`),
  test:           (pid, id)         => api.post(`/projects/${pid}/webhooks/${id}/test`),
}

// Roadmap
export const roadmapApi = {
  get: (pid) => api.get(`/projects/${pid}/roadmap`),
}
