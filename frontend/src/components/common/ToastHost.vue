<template>
  <Teleport to="body">
    <TransitionGroup name="toast" tag="div" class="toast-host" aria-live="polite">
      <div v-for="toast in toasts" :key="toast.id" class="toast" :class="`toast--${toast.type}`">
        <span class="toast__icon">
          <AppIcon :name="iconFor(toast.type)" :size="16" />
        </span>
        <p class="toast__message">{{ toast.message }}</p>
        <button type="button" class="toast__close" aria-label="Dismiss" @click="dismiss(toast.id)">
          <AppIcon name="close" :size="14" />
        </button>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, watch } from 'vue'
import AppIcon from './AppIcon.vue'
import { useToastStore } from '../../stores/toast'

const toastStore = useToastStore()
const { toasts, dismiss } = toastStore

const ICONS = {
  success: 'check',
  error: 'warning',
  warning: 'warning',
  info: 'info',
}

function iconFor(type) {
  return ICONS[type] || 'info'
}

const timers = new Map()

watch(
  toasts,
  (list) => {
    list.forEach((toast) => {
      if (timers.has(toast.id)) return
      timers.set(
        toast.id,
        setTimeout(() => {
          timers.delete(toast.id)
          dismiss(toast.id)
        }, toast.timeout),
      )
    })
    const alive = new Set(list.map((toast) => toast.id))
    timers.forEach((timer, id) => {
      if (!alive.has(id)) {
        clearTimeout(timer)
        timers.delete(id)
      }
    })
  },
  { deep: true },
)

onBeforeUnmount(() => {
  timers.forEach((timer) => clearTimeout(timer))
  timers.clear()
})
</script>

<style scoped>
.toast-host {
  position: fixed;
  top: var(--space-4);
  right: var(--space-4);
  z-index: 90;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  width: min(360px, calc(100vw - var(--space-6)));
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-left: 3px solid var(--color-text-faint);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  pointer-events: auto;
}

.toast__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  flex: none;
}

.toast__message {
  flex: 1 1 auto;
  min-width: 0;
  font-size: var(--text-base);
  line-height: var(--lh-base);
  color: var(--color-text);
}

.toast__close {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-faint);
  cursor: pointer;
}

.toast__close:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.toast--success {
  border-left-color: var(--color-success);
}

.toast--success .toast__icon {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.toast--error {
  border-left-color: var(--color-danger);
}

.toast--error .toast__icon {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.toast--warning {
  border-left-color: var(--color-warning);
}

.toast--warning .toast__icon {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.toast--info {
  border-left-color: var(--color-info);
}

.toast--info .toast__icon {
  background: var(--color-info-soft);
  color: var(--color-info);
}

.toast-enter-active,
.toast-leave-active {
  transition:
    transform var(--transition),
    opacity var(--transition);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(16px);
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .toast-enter-active,
  .toast-leave-active {
    transition-duration: 0.01ms;
  }
}
</style>