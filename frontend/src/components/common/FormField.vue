<template>
  <div class="form-field" :class="{ 'form-field--inline': inline }">
    <label v-if="label" class="form-field__label" :for="fieldId">
      {{ label }}
      <span v-if="required" class="form-field__required" aria-hidden="true">*</span>
    </label>

    <slot />

    <p v-if="error" class="form-field__error" role="alert">
      <AppIcon name="warning" :size="14" />
      <span>{{ error }}</span>
    </p>
    <p v-else-if="hint" class="form-field__hint">{{ hint }}</p>
  </div>
</template>

<script setup>
import { provide } from 'vue'
import AppIcon from './AppIcon.vue'

defineProps({
  label: { type: String, default: '' },
  error: { type: String, default: '' },
  hint: { type: String, default: '' },
  required: Boolean,
  inline: Boolean,
})

// Controls (BaseInput/BaseSelect/BaseTextarea) pick this up and apply it as
// their id, linking label -> control without wiring ids by hand everywhere.
const fieldId = `field-${Math.random().toString(36).slice(2, 9)}`
provide('meridian.formFieldId', fieldId)
</script>

<style scoped>
.form-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 0;
}

.form-field--inline {
  flex-direction: row;
  align-items: center;
  gap: var(--space-3);
}

.form-field__label {
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--text);
}

.form-field__required {
  color: var(--danger);
  margin-left: 2px;
}

.form-field__error {
  display: flex;
  align-items: flex-start;
  gap: var(--space-1);
  font-size: var(--text-sm);
  color: var(--danger);
}

.form-field__error .app-icon {
  margin-top: 2px;
}

.form-field__hint {
  font-size: var(--text-sm);
  color: var(--text-muted);
}
</style>
