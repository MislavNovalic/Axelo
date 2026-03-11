import { defineStore } from 'pinia'
import { ref } from 'vue'
import { projectsApi } from '@/api'

export const useProjectsStore = defineStore('projects', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const loading = ref(false)

  async function fetchProjects() {
    loading.value = true
    try {
      const res = await projectsApi.list()
      projects.value = res.data
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(id) {
    const res = await projectsApi.get(id)
    currentProject.value = res.data
    return res.data
  }

  async function createProject(data) {
    const res = await projectsApi.create(data)
    projects.value.unshift(res.data)
    return res.data
  }

  async function deleteProject(id) {
    await projectsApi.delete(id)
    projects.value = projects.value.filter((p) => p.id !== id)
  }

  return { projects, currentProject, loading, fetchProjects, fetchProject, createProject, deleteProject }
})
