import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)

// Global Vue error handler — catches unhandled component errors
app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue] Unhandled error:', err, '\nInfo:', info)
  // In production, send to error tracking service here
  if (import.meta.env.PROD) {
    // e.g. Sentry.captureException(err)
  }
}

// Global warn handler — log warnings in dev
app.config.warnHandler = (msg, instance, trace) => {
  if (import.meta.env.DEV) {
    console.warn('[Vue]', msg, trace)
  }
}

app.use(createPinia())
app.use(router)
app.mount('#app')
