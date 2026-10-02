<template>
  <article class="kpi" :class="`kpi--${tone}`">
    <p class="kpi__label">{{ label }}</p>
    <p v-if="loading" class="kpi__value"><LoadingSkeleton variant="block" width="72%" height="26" /></p>
    <p v-else class="kpi__value tabular">{{ value }}</p>
    <p v-if="caption" class="kpi__caption">{{ caption }}</p>
  </article>
</template>

<script setup>
import LoadingSkeleton from './LoadingSkeleton.vue'

defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '' },
  caption: { type: String, default: '' },
  tone: { type: String, default: 'neutral' },
  loading: Boolean,
})
</script>

<style scoped>
.kpi {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-width: 0;
}

.kpi__label {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.kpi__value {
  font-size: var(--text-2xl);
  font-weight: var(--fw-semibold);
  line-height: 1.15;
  letter-spacing: -0.01em;
  overflow: hidden;
  color: var(--color-text);
}

.kpi__caption {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
}

.kpi--primary .kpi__value {
  color: var(--color-primary-hover);
}

.kpi--teal .kpi__value {
  color: var(--color-teal);
}

.kpi--warning .kpi__value {
  color: var(--color-warning);
}

.kpi--success .kpi__value {
  color: var(--color-success);
}

.kpi--danger .kpi__value {
  color: var(--color-danger);
}
</style>