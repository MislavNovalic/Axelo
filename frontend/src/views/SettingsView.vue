<template>
  <div class="app-shell">
    <Navbar />
    <div class="settings-page">
      <div class="settings-header">
        <h1 class="page-title">Settings</h1>
        <p class="page-sub">Manage integrations and account security</p>
      </div>

      <!-- GitHub Integration -->
      <div class="section">
        <div class="section-header">
          <h3 class="section-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>
            GitHub Integration
          </h3>
        </div>
        <div v-if="githubInfo" class="github-connected">
          <div class="github-repo">
            <span class="repo-icon">📦</span>
            <a :href="`https://github.com/${githubInfo.repo}`" target="_blank" class="repo-link">{{ githubInfo.repo }}</a>
            <span class="connected-badge">Connected</span>
          </div>
          <p class="github-hint">Commits and PRs referencing issue keys (e.g. <code>fixes AX-42</code>) will link automatically.</p>
          <div class="webhook-box">
            <span class="wh-label">Webhook URL:</span>
            <code class="wh-url">/api/integrations/github/webhook?project_id={{ projectId }}</code>
          </div>
          <div v-if="githubInfo.recent_links?.length" class="recent-links">
            <div class="rl-title">Recent Links</div>
            <div v-for="l in githubInfo.recent_links" :key="l.id" class="rl-row">
              <span class="rl-type" :class="l.link_type">{{ l.link_type === 'pr' ? '⤴ PR' : '⬤ commit' }}</span>
              <a :href="l.gh_url" target="_blank" class="rl-title-link">{{ l.gh_title }}</a>
              <span class="rl-state" :class="l.gh_state">{{ l.gh_state }}</span>
            </div>
          </div>
          <button class="btn-danger btn-sm" @click="disconnectGitHub">Disconnect</button>
        </div>
        <div v-else class="github-connect-form">
          <p class="form-hint">Connect a GitHub repo to link PRs and commits to issues.</p>
          <div class="gh-row">
            <input v-model="ghForm.repo_owner" class="field-input" placeholder="owner (e.g. MislavNovalic)" />
            <input v-model="ghForm.repo_name" class="field-input" placeholder="repo (e.g. axelo)" />
          </div>
          <div class="gh-row">
            <input v-model="ghForm.webhook_secret" class="field-input" placeholder="Webhook secret (optional)" type="password" />
          </div>
          <button class="btn-primary btn-sm" @click="connectGitHub" :disabled="!ghForm.repo_owner || !ghForm.repo_name">
            Connect Repository
          </button>
        </div>
      </div>

      <!-- Security / 2FA -->
      <div class="section">
        <div class="section-header">
          <h3 class="section-title">🔐 Security</h3>
          <p class="section-sub">Two-factor authentication for your account.</p>
        </div>
        <TwoFactorSettings />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectsStore } from '@/store/projects'
import { githubApi } from '@/api'
import Navbar from '@/components/Navbar.vue'
import TwoFactorSettings from '@/components/TwoFactorSettings.vue'

const route = useRoute()
const projectId = computed(() => Number(route.params.id))
const projectsStore = useProjectsStore()

const githubInfo = ref(null)
const ghForm = ref({ repo_owner: '', repo_name: '', webhook_secret: '' })

async function loadGitHub() {
  try { const r = await githubApi.get(projectId.value); githubInfo.value = r.data } catch { }
}
async function connectGitHub() {
  await githubApi.connect(projectId.value, ghForm.value)
  await loadGitHub()
  ghForm.value = { repo_owner: '', repo_name: '', webhook_secret: '' }
}
async function disconnectGitHub() {
  if (!confirm('Disconnect GitHub integration?')) return
  await githubApi.disconnect(projectId.value)
  githubInfo.value = null
}

onMounted(async () => {
  if (!projectsStore.currentProject || projectsStore.currentProject.id !== projectId.value) {
    await projectsStore.fetchProject(projectId.value)
  }
  await loadGitHub()
})
</script>

<style scoped>
.app-shell { display: flex; flex-direction: column; min-height: 100vh; background: var(--bg); }
.settings-page { padding: 2rem 2.5rem; max-width: 780px; margin: 0 auto; width: 100%; box-sizing: border-box; }

.settings-header { margin-bottom: 2rem; }
.page-title { font-size: 1.5rem; font-weight: 700; color: var(--text); margin: 0 0 4px; }
.page-sub { font-size: 0.83rem; color: var(--text3); margin: 0; }

.section {
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem;
}
.section-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 1rem; gap: 8px;
}
.section-title {
  font-size: 0.95rem; font-weight: 600; color: var(--text);
  margin: 0; display: flex; align-items: center; gap: 8px;
}
.section-sub { font-size: 0.8rem; color: var(--text3); margin: 2px 0 0; }

.github-connected { display: flex; flex-direction: column; gap: 0.75rem; }
.github-repo { display: flex; align-items: center; gap: 8px; }
.repo-icon { font-size: 1rem; }
.repo-link { color: var(--accent2); text-decoration: none; font-weight: 600; }
.repo-link:hover { text-decoration: underline; }
.connected-badge { background: rgba(0,217,126,0.12); color: var(--green); font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 8px; }
.github-hint { font-size: 0.78rem; color: var(--text2); }
.github-hint code { background: var(--bg3); padding: 1px 5px; border-radius: 4px; font-family: var(--font-mono); font-size: 0.75rem; }
.webhook-box { background: var(--bg3); padding: 8px 12px; border-radius: 8px; display: flex; align-items: center; gap: 8px; }
.wh-label { font-size: 0.72rem; color: var(--text3); flex-shrink: 0; }
.wh-url { font-family: var(--font-mono); font-size: 0.7rem; color: var(--text2); }
.recent-links { margin-top: 0.5rem; }
.rl-title { font-size: 0.72rem; color: var(--text3); margin-bottom: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
.rl-row { display: flex; align-items: center; gap: 8px; padding: 4px 0; border-bottom: 1px solid var(--border); }
.rl-type { font-size: 0.68rem; font-weight: 700; font-family: var(--font-mono); min-width: 60px; }
.rl-type.pr { color: var(--accent2); }
.rl-type.commit { color: var(--text3); }
.rl-title-link { flex: 1; font-size: 0.78rem; color: var(--text); text-decoration: none; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rl-title-link:hover { color: var(--accent2); }
.rl-state { font-size: 0.65rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; text-transform: capitalize; }
.rl-state.open   { background: rgba(0,217,126,0.12); color: var(--green); }
.rl-state.merged { background: rgba(16,185,129,0.12); color: var(--accent2); }
.rl-state.closed { background: rgba(255,79,106,0.12); color: var(--red); }
.rl-state.committed { background: rgba(144,144,176,0.1); color: var(--text3); }
.github-connect-form { display: flex; flex-direction: column; gap: 0.6rem; }
.form-hint { font-size: 0.78rem; color: var(--text2); }
.gh-row { display: flex; gap: 8px; }
.gh-row .field-input { flex: 1; }

.field-input {
  width: 100%; padding: 8px 12px; border-radius: 8px;
  border: 1px solid var(--border2); background: var(--bg3);
  color: var(--text); font-size: 0.88rem; outline: none;
  box-sizing: border-box; font-family: var(--font-body);
}
.field-input:focus { border-color: var(--accent); }

.btn-sm { padding: 5px 12px; font-size: 0.78rem; }
.btn-primary {
  padding: 8px 16px; border-radius: 8px;
  background: var(--accent); color: #fff;
  border: none; cursor: pointer; font-size: 0.83rem; font-weight: 600;
  font-family: var(--font-body); transition: opacity 0.15s;
}
.btn-primary:hover { opacity: 0.88; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger {
  padding: 8px 16px; border-radius: 8px;
  background: rgba(255,79,106,0.15); color: var(--red);
  border: 1px solid rgba(255,79,106,0.3); cursor: pointer;
  font-size: 0.83rem; font-family: var(--font-body); transition: all 0.15s;
}
.btn-danger:hover { background: rgba(255,79,106,0.25); }

@media (max-width: 640px) {
  .settings-page { padding: 1rem; }
  .gh-row { flex-direction: column; }
}
</style>
