import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes = [
  { path: '/login',    name: 'Login',    component: () => import('@/views/LoginView.vue'),    meta: { public: true } },
  { path: '/register', name: 'Register', component: () => import('@/views/RegisterView.vue'), meta: { public: true } },
  { path: '/',                          name: 'Dashboard', component: () => import('@/views/DashboardView.vue') },
  { path: '/calendar',                  name: 'Calendar',  component: () => import('@/views/CalendarView.vue') },
  { path: '/projects/:id',              name: 'Board',     component: () => import('@/views/BoardView.vue') },
  { path: '/projects/:id/backlog',      name: 'Backlog',   component: () => import('@/views/BacklogView.vue') },
  { path: '/projects/:id/team',         name: 'Team',      component: () => import('@/views/TeamView.vue') },
  { path: '/projects/:id/issues/:issueId', name: 'Issue',  component: () => import('@/views/IssueView.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!to.meta.public) {
    if (!auth.token) return { name: 'Login' }
    if (!auth.user) await auth.fetchMe()
    if (!auth.user) return { name: 'Login' }
  }
})

export default router
