<template>
  <div
    class="issue-card"
    draggable="true"
    @dragstart="$emit('dragstart', issue)"
    @click="$emit('click', issue)"
  >
    <div class="card-top">
      <span class="type-badge" :class="`type-${issue.type}`">{{ typeIcon }} {{ issue.type }}</span>
      <span class="priority-badge" :class="`priority-${issue.priority}`">{{ priorityIcon }}</span>
    </div>
    <p class="card-title">{{ issue.title }}</p>
    <div class="card-footer">
      <span class="issue-key">{{ issue.key }}</span>
      <div v-if="issue.story_points" class="points-badge">{{ issue.story_points }}p</div>
      <div v-if="issue.assignee" class="assignee-chip" :title="issue.assignee.full_name">
        {{ issue.assignee.full_name[0].toUpperCase() }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ issue: Object })
defineEmits(['click', 'dragstart'])
const typeIcon = computed(() => ({ bug:'🐛', story:'📖', task:'✓', epic:'⚡' }[props.issue.type] || '•'))
const priorityIcon = computed(() => ({ critical:'🔴', high:'🟠', medium:'🟡', low:'🔵' }[props.issue.priority] || ''))
</script>

<style scoped>
.issue-card {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: 8px; padding: 10px 11px;
  cursor: pointer; transition: border-color 0.15s, transform 0.15s, box-shadow 0.15s;
}
.issue-card:hover { border-color: var(--border2); transform: translateY(-1px); box-shadow: 0 4px 14px rgba(0,0,0,0.3); }
.card-top { display: flex; align-items: center; gap: 6px; margin-bottom: 7px; }
.type-badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 2px 7px; border-radius: 4px; font-size: 0.68rem; font-weight: 500;
}
.type-badge.type-bug { background: rgba(255,79,106,0.12); color: var(--red); }
.type-badge.type-story { background: rgba(0,217,126,0.12); color: var(--green); }
.type-badge.type-task { background: rgba(16,185,129,0.12); color: var(--accent2); }
.type-badge.type-epic { background: rgba(6,182,212,0.12); color: #06b6d4; }
.priority-badge { margin-left: auto; font-size: 0.7rem; }
.card-title { font-size: 0.82rem; color: var(--text); line-height: 1.45; margin-bottom: 8px; }
.card-footer { display: flex; align-items: center; gap: 6px; }
.issue-key { font-family: var(--font-mono); font-size: 0.65rem; color: var(--text3); }
.points-badge {
  margin-left: auto; font-size: 0.65rem; padding: 1px 6px;
  border-radius: 3px; background: var(--bg2); color: var(--text3);
}
.assignee-chip {
  width: 18px; height: 18px; border-radius: 50%; background: var(--accent);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.55rem; font-weight: 700; color: #fff;
}
</style>
