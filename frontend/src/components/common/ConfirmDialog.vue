<template>
  <AppModal
    :open="open"
    :title="title"
    size="sm"
    :close-on-backdrop="!loading"
    @close="onCancel"
  >
    <div class="confirm">
      <span class="confirm__icon" :class="`confirm__icon--${tone}`">
        <AppIcon :name="tone === 'danger' ? 'warning' : 'info'" :size="20" />
      </span>
      <div class="confirm__text">
        <p>{{ message }}</p>
        <slot />
      </div>
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="loading" @click="onCancel">
        {{ cancelLabel }}
      </BaseButton>
      <BaseButton
        :variant="tone === 'danger' ? 'danger' : 'primary'"
        :loading="loading"
        @click="emit('confirm')"
      >
        {{ confirmLabel }}
      </BaseButton>
    </template>
  </AppModal>
</template>

<script setup>
import AppModal from './AppModal.vue'
import BaseButton from './BaseButton.vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  open: Boolean,
  title: { type: String, default: 'Are you sure?' },
  message: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Confirm' },
  cancelLabel: { type: String, default: 'Cancel' },
  tone: { type: String, default: 'primary' },
  loading: Boolean,
})

const emit = defineEmits(['confirm', 'cancel'])

function onCancel() {
  if (!props.loading) emit('cancel')
}
</script>

<style scoped>
.confirm {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
}

.confirm__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  flex: none;
}

.confirm__icon--danger {
  background: var(--danger-soft);
  color: var(--danger);
}

.confirm__icon--primary {
  background: var(--accent-soft);
  color: var(--accent-text);
}

.confirm__text {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  color: var(--text-muted);
  line-height: var(--lh-base);
}
</style>
