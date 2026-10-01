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
  border-radius: 999px;
  font-weight: var(--fw-medium);
  white-space: nowrap;
  line-height: 1;
}

.badge--md {
  font-size: var(--text-xs);
  padding: 5px 10px;
}

.badge--sm {
  font-size: 11px;
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
  background: var(--surface-3);
  color: var(--text-muted);
}

.badge--accent {
  background: var(--accent-soft);
  color: var(--accent-text);
}

.badge--success {
  background: var(--success-soft);
  color: var(--success);
}

.badge--warning {
  background: var(--warning-soft);
  color: var(--warning);
}

.badge--danger {
  background: var(--danger-soft);
  color: var(--danger);
}

.badge--info {
  background: var(--info-soft);
  color: var(--info);
}
</style>
