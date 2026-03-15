<template>
  <div class="sprint-planner">
    <div class="planner-header">
      <div>
        <h1 class="page-title">
          <span class="ai-spark">✦</span> AI Sprint Planner
        </h1>
        <p class="page-sub">
          {{ project?.name }} · AI-powered sprint composition based on velocity and priority
        </p>
      </div>
    </div>

    <!-- Config panel -->
    <div class="config-card">
      <div class="config-row">
        <div class="config-field">
          <label class="field-label">Sprint capacity (story points)</label>
          <input
            v-model.number="capacity"
            type="number"
            min="1"
            max="500"
            class="config-input"
            placeholder="Auto-detect from velocity"
          />
        </div>
        <div class="config-field">
          <label class="field-label">Sprint focus</label>
          <select v-model="focus" class="config-input">
            <option value="">Balanced (default)</option>
            <option value="stability">Stability — prioritise bugs</option>
            <option value="features">Features — new functionality</option>
            <option value="tech debt">Tech Debt — refactoring and improvements</option>
            <option value="high priority only">High priority only</option>
          </select>
        </div>
        <button
          class="btn-plan"
          @click="generatePlan"
          :disabled="loading"
        >
          <span v-if="!loading">✦ Generate Plan</span>
          <span v-else class="btn-loader">
            <span></span><span></span><span></span>
          </span>
        </button>
      </div>
    </div>

    <!-- Error -->
    <transition name="fade">
      <div v-if="error" class="error-banner">⚠ {{ error }}</div>
    </transition>

    <!-- Results -->
    <transition name="fade">
      <div v-if="plan" class="results">
        <!-- Metrics strip -->
        <div class="metrics-strip">
          <div class="metric-card">
            <div class="metric-value">{{ plan.recommended_issues.length }}</div>
            <div class="metric-label">Issues</div>
          </div>
          <div class="metric-card accent">
            <div class="metric-value">{{ plan.estimated_points }}</div>
            <div class="metric-label">Est. Points</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{{ plan.capacity }}</div>
            <div class="metric-label">Capacity</div>
          </div>
          <div class="metric-card">
            <div class="metric-value">{{ plan.avg_velocity }}</div>
            <div class="metric-label">Avg Velocity</div>
          </div>
          <div class="metric-card small">
            <div class="metric-label" style="margin-bottom:2px">{{ plan.model }}</div>
            <div class="metric-label">{{ plan.tokens_used?.toLocaleString() }} tokens</div>
          </div>
        </div>

        <!-- Reasoning -->
        <div class="reasoning-box">
          <div class="reasoning-label">✦ AI Reasoning</div>
          <p class="reasoning-text">{{ plan.reasoning }}</p>
        </div>

        <!-- Warnings -->
        <div v-if="plan.warnings?.length" class="warnings-list">
          <div v-for="w in plan.warnings" :key="w" class="warning-row">⚠ {{ w }}</div>
        </div>

        <!-- Issue list -->
        <div class="issues-section">
          <div class="section-header-row">
            <h3 class="section-title">Recommended Issues</h3>
            <button class="btn-create-sprint" @click="createSprintFromPlan" :disabled="creating">
              {{ creating ? 'Creating…' : '+ Create Sprint from this Plan' }}
            </button>
          </div>
          <div class="issue-list">
            <div
              v-for="issue in plan.recommended_issues"
              :key="issue.id"
              class="issue-row"
              @click="$router.push(`/projects/${projectId}/issues/${issue.id}`)"
            >
              <span class="type-icon">{{ typeIcon(issue.type) }}</span>
              <span class="issue-key">{{ issue.key }}</span>
              <span class="issue-title">{{ issue.title }}</span>
              <span class="priority-badge" :class="issue.priority">{{ issue.priority }}</span>
              <span class="pts-badge" v-if="issue.story_points">{{ issue.story_points }}pt</span>
              <span class="pts-badge empty" v-else>?pt</span>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- Empty state -->
    <div v-if="!plan && !loading && !error" class="empty-state">
      <div class="empty-icon">✦</div>
      <p>Configure capacity and focus above, then click <strong>Generate Plan</strong> to get an AI-recommended sprint.</p>
      <p class="empty-sub">Axelo will analyse your velocity history, backlog priorities, and team capacity.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { projectsApi, sprintsApi } from '@/api'
import api from '@/api'

const route = useRoute()
const projectId = parseInt(route.params.id)

const project  = ref(null)
const capacity = ref(null)
const focus    = ref('')
const loading  = ref(false)
const creating = ref(false)
const error    = ref('')
const plan     = ref(null)

function typeIcon(t) {
  return { bug: '🐛', story: '📖', task: '✅', epic: '⚡' }[t] ?? '•'
}

async function generatePlan() {
  loading.value = true
  error.value   = ''
  plan.value    = null
  try {
    const res = await api.post(`/projects/${projectId}/ai/sprint-plan`, {
      sprint_capacity_points: capacity.value || null,
      focus: focus.value || null,
    })
    plan.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'AI request failed. Check your API key and try again.'
  } finally {
    loading.value = false }
}

async function createSprintFromPlan() {
  if (!plan.value?.recommended_issues?.length) return
  creating.value = true
  try {
    const today = new Date()
    const twoWeeks = new Date(today.getTime() + 14 * 86400 * 1000)
    const sprint = await sprintsApi.create(projectId, {
      name: `AI Sprint — ${today.toLocaleDateString()}`,
      goal: `AI-planned sprint (${plan.value.estimated_points} pts, focus: ${focus.value || 'balanced'})`,
      start_date: today.toISOString(),
      end_date: twoWeeks.toISOString(),
    })
    // Assign issues to sprint
    for (const issue of plan.value.recommended_issues) {
      await api.patch(`/projects/${projectId}/issues/${issue.id}`, {
        sprint_id: sprint.data.id,
      })
    }
    alert(`Sprint created with ${plan.value.recommended_issues.length} issues!`)
  } catch (e) {
    alert('Failed to create sprint: ' + (e.response?.data?.detail || e.message))
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  const res = await projectsApi.get(projectId)
  project.value = res.data
})
</script>

<style scoped>
.sprint-planner { padding: 2rem; max-width: 900px; margin: 0 auto; }
.planner-header { margin-bottom: 1.5rem; }
.page-title {
  font-family: var(--font-display); font-size: 1.6rem; font-weight: 800;
  color: var(--text); margin-bottom: 0.2rem; display: flex; align-items: center; gap: 8px;
}
.ai-spark { color: #06b6d4; animation: sparkle 2s ease-in-out infinite; }
@keyframes sparkle { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.6;transform:scale(1.3)} }
.page-sub { font-size: 0.85rem; color: var(--text2); }
.config-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: 1.5rem; }
.config-row { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
.config-field { display: flex; flex-direction: column; gap: 5px; flex: 1; min-width: 160px; }
.field-label { font-size: 0.75rem; font-weight: 600; color: var(--text2); }
.config-input { padding: 9px 12px; border: 1.5px solid var(--border2); border-radius: 8px; background: var(--bg); color: var(--text); font-size: 0.85rem; outline: none; }
.config-input:focus { border-color: #06b6d4; box-shadow: 0 0 0 3px rgba(6,182,212,0.12); }
.btn-plan {
  padding: 10px 22px; background: linear-gradient(135deg, #06b6d4, #10b981);
  color: #fff; border: none; border-radius: 10px; font-size: 0.88rem; font-weight: 700;
  cursor: pointer; white-space: nowrap; min-height: 42px; display: flex; align-items: center;
  box-shadow: 0 4px 16px rgba(6,182,212,0.3); transition: opacity 0.15s, transform 0.15s;
}
.btn-plan:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(6,182,212,0.4); }
.btn-plan:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-loader { display: flex; gap: 4px; align-items: center; }
.btn-loader span { width: 7px; height: 7px; border-radius: 50%; background: #fff; animation: bounce 0.8s ease-in-out infinite; }
.btn-loader span:nth-child(2) { animation-delay: 0.15s; } .btn-loader span:nth-child(3) { animation-delay: 0.3s; }
@keyframes bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-7px)} }
.error-banner { background: rgba(255,79,106,0.1); border: 1px solid rgba(255,79,106,0.3); border-radius: 10px; padding: 12px 16px; font-size: 0.85rem; color: var(--red); margin-bottom: 1rem; }
.results { display: flex; flex-direction: column; gap: 1rem; }
.metrics-strip { display: flex; gap: 10px; flex-wrap: wrap; }
.metric-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 12px 16px; text-align: center; flex: 1; min-width: 80px; }
.metric-card.accent { background: rgba(6,182,212,0.08); border-color: rgba(6,182,212,0.25); }
.metric-card.small { flex: 0 0 auto; }
.metric-value { font-family: var(--font-display); font-size: 1.6rem; font-weight: 800; color: var(--text); line-height: 1; }
.metric-card.accent .metric-value { color: #06b6d4; }
.metric-label { font-size: 0.72rem; color: var(--text3); margin-top: 3px; font-family: var(--font-mono); }
.reasoning-box { background: rgba(6,182,212,0.05); border: 1px solid rgba(6,182,212,0.2); border-radius: 12px; padding: 1rem 1.25rem; }
.reasoning-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #06b6d4; margin-bottom: 0.5rem; }
.reasoning-text { font-size: 0.87rem; color: var(--text2); line-height: 1.65; margin: 0; }
.warnings-list { display: flex; flex-direction: column; gap: 5px; }
.warning-row { background: rgba(255,209,30,0.08); border: 1px solid rgba(255,209,30,0.25); border-radius: 8px; padding: 8px 12px; font-size: 0.82rem; color: var(--yellow); }
.issues-section { background: var(--bg2); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; }
.section-header-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--border); }
.section-title { font-size: 0.9rem; font-weight: 700; color: var(--text); margin: 0; }
.btn-create-sprint { padding: 7px 14px; background: #06b6d4; color: #fff; border: none; border-radius: 8px; font-size: 0.8rem; font-weight: 700; cursor: pointer; transition: opacity 0.15s; }
.btn-create-sprint:disabled { opacity: 0.5; cursor: not-allowed; }
.issue-list { display: flex; flex-direction: column; }
.issue-row { display: flex; align-items: center; gap: 10px; padding: 10px 16px; border-bottom: 1px solid var(--border); font-size: 0.83rem; cursor: pointer; transition: background 0.12s; }
.issue-row:last-child { border-bottom: none; }
.issue-row:hover { background: var(--bg3); }
.type-icon { flex-shrink: 0; font-size: 0.9rem; }
.issue-key { font-family: var(--font-mono); font-size: 0.75rem; color: var(--text3); flex-shrink: 0; }
.issue-title { flex: 1; color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.priority-badge { padding: 2px 7px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; text-transform: capitalize; flex-shrink: 0; }
.priority-badge.critical, .priority-badge.high { background: rgba(255,79,106,0.12); color: var(--red); }
.priority-badge.medium { background: rgba(255,209,30,0.12); color: var(--yellow); }
.priority-badge.low { background: var(--bg3); color: var(--text3); }
.pts-badge { font-family: var(--font-mono); font-size: 0.72rem; background: rgba(16,185,129,0.1); color: var(--accent2); border-radius: 4px; padding: 2px 6px; flex-shrink: 0; }
.pts-badge.empty { background: var(--bg3); color: var(--text3); }
.empty-state { text-align: center; padding: 3rem 2rem; color: var(--text3); }
.empty-icon { font-size: 2.5rem; color: #06b6d4; margin-bottom: 1rem; opacity: 0.5; }
.empty-state p { font-size: 0.9rem; line-height: 1.6; max-width: 480px; margin: 0 auto 0.5rem; }
.empty-sub { font-size: 0.8rem !important; }
.fade-enter-active { transition: opacity 0.35s, transform 0.35s; }
.fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from { opacity: 0; transform: translateY(8px); }
.fade-leave-to { opacity: 0; }

/* ── Responsive ─────────────────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .sprint-planner { padding: 1.5rem; }
  .config-row { flex-direction: column; }
  .btn-plan { width: 100%; justify-content: center; }
  .metrics-strip { flex-wrap: wrap; }
  .metric-card { min-width: calc(50% - 10px); }
}
@media (max-width: 640px) {
  .sprint-planner { padding: 1rem; }
  .section-header-row { flex-direction: column; align-items: flex-start; gap: 8px; }
  .btn-create-sprint { width: 100%; }
  .issue-row { flex-wrap: wrap; }
  .metric-card { min-width: calc(50% - 10px); }
}
</style>
