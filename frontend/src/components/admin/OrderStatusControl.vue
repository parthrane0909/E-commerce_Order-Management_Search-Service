<template>
  <div class="status-control">
    <span class="status-control__label">Update status</span>
    <div class="status-control__row">
      <BaseSelect
        class="status-control__select"
        :model-value="pending || status"
        :options="statusOptions()"
        :disabled="updating"
        aria-label="Order status"
        @update:model-value="emit('change', $event)"
      />
      <span v-if="updating" class="status-control__spinner" role="status" aria-label="Saving status" />
    </div>
  </div>
</template>

<script setup>
import BaseSelect from '../common/BaseSelect.vue'
import { statusOptions } from '../../utils/status'

defineProps({
  status: { type: String, required: true },
  pending: { type: String, default: '' },
  updating: Boolean,
})

const emit = defineEmits(['change'])
</script>

<style scoped>
.status-control {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.status-control__label {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.status-control__row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.status-control__select {
  min-width: 170px;
}

.status-control__spinner {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid var(--accent);
  border-top-color: transparent;
  animation: status-spin 700ms linear infinite;
  flex: none;
}

@keyframes status-spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
