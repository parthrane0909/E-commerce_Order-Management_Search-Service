<template>
  <div class="login-view">
    <div class="login-view__card">
      <div class="login-view__header">
        <RouterLink to="/" class="brand">
          <span class="brand__mark" aria-hidden="true">M</span>
          <span class="brand__name">Meridian</span>
        </RouterLink>
      </div>
      <LoginForm @success="onSuccess" />
    </div>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import LoginForm from '../components/auth/LoginForm.vue'

const router = useRouter()
const route = useRoute()

function onSuccess() {
  const redirect = route.query.redirect || '/'
  router.replace(redirect)
}
</script>

<style scoped>
.login-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6) var(--space-4);
  background: var(--color-bg);
}

.login-view__card {
  width: 100%;
  max-width: 400px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
}

.login-view__header {
  padding: var(--space-5) var(--space-5) var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text);
  font-weight: var(--fw-semibold);
  font-size: var(--text-md);
}

.brand__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
}
</style>