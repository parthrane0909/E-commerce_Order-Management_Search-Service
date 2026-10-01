<template>
  <div class="alert" :class="`alert--${tone}`" :role="role">
    <AppIcon :name="icon" :size="16" class="alert__icon" />
    <div class="alert__content">
      <p v-if="title" class="alert__title">{{ title }}</p>
      <div class="alert__message"><slot>{{ message }}</slot></div>
    </div>
    <button
      v-if="dismissible"
      type="button"
      class="alert__close"
      aria-label="Dismiss"
      @click="emit('dismiss')"
    >
      <AppIcon name="close" :size="14" />
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  tone: { type: String, default: 'info' },
  title: { type: String, default: '' },
  message: { type: String, default: '' },
  dismissible: Boolean,
})

const emit = defineEmits(['dismiss'])

const ICONS = {
  info: 'info',
  success: 'check',
  warning: 'warning',
  danger: 'warning',
}

const icon = computed(() => ICONS[props.tone] || 'info')
const role = computed(() => (props.tone === 'danger' || props.tone === 'warning' ? 'alert' : 'status'))
</script>

<style scoped>
.alert {
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  padding: var(--space-3);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface-2);
  font-size: var(--text-base);
}

.alert__icon {
  margin-top: 2px;
  flex: none;
}

.alert__content {
  flex: 1 1 auto;
  min-width: 0;
}

.alert__title {
  font-weight: var(--fw-semibold);
  margin-bottom: 2px;
}

.alert__message {
  color: var(--text-muted);
  line-height: var(--lh-base);
}

.alert__close {
  flex: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
}

.alert__close:hover {
  background: rgba(18, 22, 29, 0.06);
}

.alert--info {
  background: var(--info-soft);
  border-color: var(--info-border);
}

.alert--info .alert__icon,
.alert--info .alert__message {
  color: var(--info);
}

.alert--success {
  background: var(--success-soft);
  border-color: var(--success-border);
}

.alert--success .alert__icon,
.alert--success .alert__message {
  color: var(--success);
}

.alert--warning {
  background: var(--warning-soft);
  border-color: var(--warning-border);
}

.alert--warning .alert__icon,
.alert--warning .alert__message {
  color: var(--warning);
}

.alert--danger {
  background: var(--danger-soft);
  border-color: var(--danger-border);
}

.alert--danger .alert__icon,
.alert--danger .alert__message {
  color: var(--danger);
}
</style>
