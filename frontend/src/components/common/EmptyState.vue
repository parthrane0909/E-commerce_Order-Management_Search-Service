<template>
  <div class="empty">
    <span class="empty__icon">
      <AppIcon :name="icon" :size="24" />
    </span>
    <h3 class="empty__title">{{ title }}</h3>
    <p v-if="message" class="empty__message">{{ message }}</p>
    <div v-if="$slots.actions" class="empty__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
import AppIcon from './AppIcon.vue'

defineProps({
  title: { type: String, required: true },
  message: { type: String, default: '' },
  icon: { type: String, default: 'inbox' },
})
</script>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--space-2);
  padding: var(--space-7) var(--space-4);
}

.empty__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--surface-3);
  color: var(--text-muted);
  margin-bottom: var(--space-1);
}

.empty__title {
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
}

.empty__message {
  max-width: 440px;
  color: var(--text-muted);
  font-size: var(--text-base);
}

.empty__actions {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-3);
  flex-wrap: wrap;
  justify-content: center;
}
</style>
