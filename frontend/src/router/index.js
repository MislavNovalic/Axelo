import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes = [
  { path: '/login',    name: 'Login',    component: () => import('@/views/LoginView.vue'),    meta: { public: true } },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterView.vue'), meta: { public: true } },
  // OAuth callback landing — handled by auth store in App.vue
  { path: '/oauth/:provider/callback', name: 'OAuthCallback', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
  { path: '/',                                   name: 'Dashboard', component: () => import('@/views/DashboardView.vue') },
  { path: '/calendar',                           name: 'Calendar',  component: () => import('@/views/CalendarView.vue') },
  { path: '/projects/:id',                       name: 'Board',     component: () => import('@/views/BoardView.vue') },
  { path: '/projects/:id/backlog',               name: 'Backlog',   component: () => import('@/views/BacklogView.vue') },
  { path: '/projects/:id/team',                  name: 'Team',      component: () => import('@/views/TeamView.vue') },
  { path: '/projects/:id/reports',               name: 'Reports',   component: () => import('@/views/ReportsView.vue') },
  { path: '/projects/:id/roadmap',               name: 'Roadmap',   component: () => import('@/views/RoadmapView.vue') },
  { path: '/projects/:id/issues/:issueId',       name: 'Issue',     component: () => import('@/views/IssueView.vue') },
  { path: '/verify-email', name: 'VerifyEmail', component: () => import('@/views/VerifyEmailView.vue'), meta: { public: true } },
  // Phase 4
  { path: '/orgs',                               name: 'Orgs',         component: () => import('@/views/OrgsView.vue') },
  { path: '/projects/:id/ai/sprint-planner',     name: 'AiPlanner',   component: () => import('@/views/AiSprintPlannerView.vue') },
  { path: '/projects/:id/import',                name: 'Importer',    component: () => import('@/views/ImporterView.vue') },
  { path: '/projects/:id/settings',             name: 'Settings',    component: () => import('@/views/SettingsView.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  // Consume OAuth token from URL query string (?token=xxx)
  auth.consumeOAuthToken()

  if (!to.meta.public) {
    if (!auth.token) return { name: 'Login' }
    if (!auth.user) await auth.fetchMe()
    if (!auth.user) return { name: 'Login' }
  }
})

export default router
