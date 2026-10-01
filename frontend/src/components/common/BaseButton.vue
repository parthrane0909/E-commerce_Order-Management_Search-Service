<template>
  <button
    class="btn"
    :class="[
      `btn--${variant}`,
      `btn--${size}`,
      {
        'btn--block': block,
        'btn--loading': loading,
      },
    ]"
    :type="type"
    :disabled="disabled || loading"
    :aria-busy="loading ? 'true' : undefined"
  >
    <span v-if="loading" class="btn__spinner" aria-hidden="true" />
    <AppIcon v-else-if="icon" :name="icon" :size="size === 'sm' ? 15 : 16" />
    <span class="btn__label"><slot /></span>
  </button>
</template>

<script setup>
import AppIcon from './AppIcon.vue'

// Single root element: class/style/listeners from the parent fall through and
// merge with the button's own classes automatically.
const props = defineProps({
  variant: { type: String, default: 'primary' },
  size: { type: String, default: 'md' },
  type: { type: String, default: 'button' },
  loading: Boolean,
  disabled: Boolean,
  block: Boolean,
  icon: String,
})
</script>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-weight: var(--fw-medium);
  font-size: var(--text-base);
  line-height: 1;
  cursor: pointer;
  white-space: nowrap;
  transition:
    background-color var(--transition),
    border-color var(--transition),
    color var(--transition),
    box-shadow var(--transition);
}

.btn--md {
  height: 38px;
  padding: 0 var(--space-4);
}

.btn--sm {
  height: 30px;
  padding: 0 var(--space-3);
  font-size: var(--text-sm);
}

.btn--block {
  width: 100%;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.btn__label {
  display: inline-block;
}

/* ---------------- variants ---------------- */

.btn--primary {
  background: var(--accent);
  color: var(--on-accent);
  box-shadow: var(--shadow-1);
}

.btn--primary:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn--primary:active:not(:disabled) {
  background: var(--accent-active);
}

.btn--secondary {
  background: var(--surface);
  border-color: var(--border-strong);
  color: var(--text);
}

.btn--secondary:hover:not(:disabled) {
  background: var(--surface-2);
  border-color: var(--border-strong);
}

.btn--secondary:active:not(:disabled) {
  background: var(--surface-3);
}

.btn--ghost {
  background: transparent;
  color: var(--text-muted);
}

.btn--ghost:hover:not(:disabled) {
  background: var(--surface-2);
  color: var(--text);
}

.btn--danger {
  background: var(--danger);
  color: var(--on-accent);
}

.btn--danger:hover:not(:disabled) {
  background: var(--danger-hover);
}

.btn--link {
  background: transparent;
  color: var(--accent-text);
  height: auto;
  padding: 0;
}

.btn--link:hover:not(:disabled) {
  text-decoration: underline;
}

/* ---------------- loading ---------------- */

.btn__spinner {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid currentColor;
  border-top-color: transparent;
  animation: btn-spin 700ms linear infinite;
}

@keyframes btn-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
