import { defineStore } from 'pinia'
import { ref } from 'vue'
import { issuesApi } from '@/api'

export const useIssuesStore = defineStore('issues', () => {
  const issues = ref([])
  const currentIssue = ref(null)
  const loading = ref(false)

  async function fetchIssues(projectId, params = {}) {
    loading.value = true
    try {
      const res = await issuesApi.list(projectId, params)
      issues.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchIssue(projectId, issueId) {
    const res = await issuesApi.get(projectId, issueId)
    currentIssue.value = res.data
    return res.data
  }

  async function createIssue(projectId, data) {
    const res = await issuesApi.create(projectId, data)
    issues.value.push(res.data)
    return res.data
  }

  async function updateIssue(projectId, issueId, data) {
    const res = await issuesApi.update(projectId, issueId, data)
    const idx = issues.value.findIndex((i) => i.id === issueId)
    if (idx !== -1) issues.value[idx] = res.data
    if (currentIssue.value?.id === issueId) currentIssue.value = res.data
    return res.data
  }

  async function deleteIssue(projectId, issueId) {
    await issuesApi.delete(projectId, issueId)
    issues.value = issues.value.filter((i) => i.id !== issueId)
  }

  async function addComment(projectId, issueId, body) {
    const res = await issuesApi.addComment(projectId, issueId, { body })
    if (currentIssue.value?.id === issueId) {
      currentIssue.value.comments.push(res.data)
    }
    return res.data
  }

  const byStatus = (status) => issues.value.filter((i) => i.status === status)

  return { issues, currentIssue, loading, fetchIssues, fetchIssue, createIssue, updateIssue, deleteIssue, addComment, byStatus }
})
