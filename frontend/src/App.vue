<template>
  <ErrorBoundary>
    <router-view />
    <SearchPalette />
    <KeyboardShortcutsHelp />
  </ErrorBoundary>
</template>

<script setup>
import ErrorBoundary from '@/components/ErrorBoundary.vue'
import SearchPalette from '@/components/SearchPalette.vue'
import KeyboardShortcutsHelp from '@/components/KeyboardShortcutsHelp.vue'
</script>
