<template>
  <span class="badge" :class="[`badge--${tone}`, `badge--${size}`]">
    <span v-if="dot" class="badge__dot" aria-hidden="true" />
    <slot />
  </span>
</template>

<script setup>
defineProps({
  tone: { type: String, default: 'neutral' },
  size: { type: String, default: 'md' },
  dot: Boolean,
})
</script>

<style scoped>
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  border-radius: var(--radius-full);
  font-weight: var(--fw-medium);
  white-space: nowrap;
  line-height: 1;
}

.badge--md {
  font-size: var(--text-xs);
  padding: 5px 10px;
}

.badge--sm {
  font-size: 10px;
  padding: 3px 8px;
}

.badge__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex: none;
}

.badge--neutral {
  background: var(--color-border);
  color: var(--color-text-muted);
}

.badge--primary {
  background: var(--color-primary-soft);
  color: var(--color-primary-hover);
}

.badge--success {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.badge--warning {
  background: var(--color-warning-soft);
  color: var(--color-warning);
}

.badge--danger {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.badge--info {
  background: var(--color-info-soft);
  color: var(--color-info);
}

.badge--teal {
  background: var(--color-teal-soft);
  color: var(--color-teal);
}
</style>