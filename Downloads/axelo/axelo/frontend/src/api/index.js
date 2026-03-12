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

// Auth
export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (email, password) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    return api.post('/auth/login', form)
  },
  me: () => api.get('/auth/me'),
}

// Projects
export const projectsApi = {
  list: (params) => api.get('/projects/', { params }),
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
  list: (projectId, params) => api.get(`/projects/${projectId}/sprints/`, { params }),
  create: (projectId, data) => api.post(`/projects/${projectId}/sprints/`, data),
  update: (projectId, sprintId, data) => api.patch(`/projects/${projectId}/sprints/${sprintId}`, data),
  delete: (projectId, sprintId) => api.delete(`/projects/${projectId}/sprints/${sprintId}`),
  burndown: (projectId, sprintId) => api.get(`/projects/${projectId}/sprints/${sprintId}/burndown`),
}

// Calendar
export const calendarApi = {
  getMonth: (year, month) => api.get('/calendar/', { params: { year, month } }),
  setDueDate: (issueId, due_date) => api.patch(`/calendar/${issueId}/due-date`, { due_date }),
}

// Notifications
export const notificationsApi = {
  list: (params) => api.get('/notifications/', { params }),
  unreadCount: () => api.get('/notifications/unread-count'),
  markRead: (id) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.patch('/notifications/read-all'),
}

// Search
export const searchApi = {
  search: (q, project_id) => api.get('/search/', { params: { q, project_id } }),
}

// Templates
export const templatesApi = {
  list: (projectId) => api.get(`/projects/${projectId}/templates/`),
  create: (projectId, data) => api.post(`/projects/${projectId}/templates/`, data),
  delete: (projectId, templateId) => api.delete(`/projects/${projectId}/templates/${templateId}`),
}

export default api
