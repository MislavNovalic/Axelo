<template>
  <div class="burndown-wrap">
    <div class="burndown-header">
      <span class="burndown-title">Burndown</span>
      <span class="burndown-pts" v-if="data">{{ remaining }} / {{ data.total_points }} pts remaining</span>
    </div>
    <div v-if="!data || !data.days?.length" class="burndown-empty">
      {{ loading ? 'Loading…' : 'No story-point data for this sprint.' }}
    </div>
    <canvas v-else ref="canvasRef" class="burndown-canvas"></canvas>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { sprintsApi } from '@/api'

const props = defineProps({
  projectId: { type: Number, required: true },
  sprintId: { type: Number, required: true },
})

const canvasRef = ref(null)
const data = ref(null)
const loading = ref(false)
let chartInstance = null

const remaining = computed(() => {
  if (!data.value?.days?.length) return 0
  return data.value.days[data.value.days.length - 1]?.actual ?? data.value.total_points
})

async function fetchBurndown() {
  if (!props.sprintId) return
  loading.value = true
  try {
    const res = await sprintsApi.burndown(props.projectId, props.sprintId)
    data.value = res.data
  } catch {
    data.value = null
  } finally {
    loading.value = false
  }
}

async function renderChart() {
  if (!canvasRef.value || !data.value?.days?.length) return

  // Lazy-load Chart.js from CDN if not already loaded
  if (!window.Chart) {
    await new Promise((resolve, reject) => {
      const s = document.createElement('script')
      s.src = 'https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js'
      s.onload = resolve
      s.onerror = reject
      document.head.appendChild(s)
    })
  }

  if (chartInstance) chartInstance.destroy()

  const labels = data.value.days.map(d => d.date.slice(5)) // MM-DD
  const ideal = data.value.days.map(d => d.ideal)
  const actual = data.value.days.map(d => d.actual)

  chartInstance = new window.Chart(canvasRef.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Ideal',
          data: ideal,
          borderColor: 'rgba(128,128,200,0.5)',
          borderDash: [5, 3],
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0,
        },
        {
          label: 'Actual',
          data: actual,
          borderColor: '#5c4fff',
          backgroundColor: 'rgba(92,79,255,0.08)',
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: '#5c4fff',
          fill: true,
          tension: 0.2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      animation: false,
      plugins: {
        legend: {
          labels: { color: 'rgba(144,144,176,0.9)', font: { size: 10 }, boxWidth: 12 },
        },
      },
      scales: {
        x: {
          ticks: { color: 'rgba(144,144,176,0.7)', font: { size: 9 } },
          grid: { color: 'rgba(255,255,255,0.04)' },
        },
        y: {
          beginAtZero: true,
          ticks: { color: 'rgba(144,144,176,0.7)', font: { size: 9 } },
          grid: { color: 'rgba(255,255,255,0.04)' },
        },
      },
    },
  })
}

watch(data, () => {
  // Wait for DOM to update before rendering
  setTimeout(renderChart, 50)
})

watch(() => props.sprintId, fetchBurndown)
onMounted(fetchBurndown)

onUnmounted(() => {
  chartInstance?.destroy()
})
</script>

<style scoped>
.burndown-wrap {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: 10px; padding: 12px; margin-top: 12px;
}
.burndown-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;
}
.burndown-title { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.07em; color: var(--text3); }
.burndown-pts { font-size: 0.72rem; color: var(--text2); }
.burndown-empty { font-size: 0.75rem; color: var(--text3); text-align: center; padding: 12px 0; }
.burndown-canvas { width: 100% !important; max-height: 140px; }
</style>
