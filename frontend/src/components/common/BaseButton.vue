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

.btn--lg {
  height: 44px;
  padding: 0 var(--space-6);
  font-size: var(--text-md);
}

.btn--md {
  height: 38px;
  padding: 0 var(--space-4);
}

.btn--sm {
  height: 32px;
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
  background: var(--color-primary);
  color: var(--color-on-primary);
  box-shadow: var(--shadow-sm);
}

.btn--primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
  box-shadow: var(--shadow-md);
}

.btn--primary:active:not(:disabled) {
  background: var(--color-primary-active);
  box-shadow: var(--shadow-sm);
}

.btn--primary:focus-visible {
  outline: none;
  box-shadow: var(--shadow-sm), var(--focus-ring);
}

.btn--secondary {
  background: var(--color-surface);
  border-color: var(--color-border-strong);
  color: var(--color-text);
}

.btn--secondary:hover:not(:disabled) {
  background: var(--color-surface-hover);
  border-color: var(--color-border-strong);
}

.btn--secondary:active:not(:disabled) {
  background: var(--color-border);
}

.btn--secondary:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.btn--ghost {
  background: transparent;
  color: var(--color-text-muted);
}

.btn--ghost:hover:not(:disabled) {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.btn--ghost:active:not(:disabled) {
  background: var(--color-border);
}

.btn--ghost:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.btn--danger {
  background: var(--color-danger);
  color: var(--color-on-primary);
  box-shadow: var(--shadow-sm);
}

.btn--danger:hover:not(:disabled) {
  background: var(--color-danger-hover);
  box-shadow: var(--shadow-md);
}

.btn--danger:active:not(:disabled) {
  background: var(--color-danger-hover);
  box-shadow: var(--shadow-sm);
}

.btn--danger:focus-visible {
  outline: none;
  box-shadow: var(--shadow-sm), 0 0 0 3px rgba(198, 40, 40, 0.35);
}

.btn--teal {
  background: var(--color-teal);
  color: var(--color-on-primary);
  box-shadow: var(--shadow-sm);
}

.btn--teal:hover:not(:disabled) {
  background: var(--color-teal-hover);
  box-shadow: var(--shadow-md);
}

.btn--teal:active:not(:disabled) {
  background: var(--color-teal-hover);
  box-shadow: var(--shadow-sm);
}

.btn--teal:focus-visible {
  outline: none;
  box-shadow: var(--shadow-sm), var(--focus-ring-teal);
}

.btn--link {
  background: transparent;
  color: var(--color-primary);
  height: auto;
  padding: 0;
}

.btn--link:hover:not(:disabled) {
  text-decoration: underline;
}

.btn--link:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
  border-radius: var(--radius-sm);
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

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .btn__spinner {
    animation-duration: 0.01ms;
    animation-iteration-count: 1;
  }
}
</style>