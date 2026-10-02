<template>
  <div
    class="field field--textarea"
    :class="[{ 'field--invalid': invalid, 'field--disabled': disabled }, attrs.class]"
    :style="attrs.style"
  >
    <textarea
      class="field__control"
      v-bind="controlBindings"
      :value="modelValue"
      :placeholder="placeholder"
      :rows="rows"
      :disabled="disabled || undefined"
      :aria-invalid="invalid ? 'true' : undefined"
      @input="onInput"
    />
  </div>
</template>

<script setup>
import { computed, inject, useAttrs } from 'vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  placeholder: { type: String, default: '' },
  rows: { type: [Number, String], default: 4 },
  disabled: Boolean,
  invalid: Boolean,
})

const emit = defineEmits(['update:modelValue'])
const attrs = useAttrs()
const injectedId = inject('meridian.formFieldId', null)

const controlBindings = computed(() => {
  const { class: _class, style: _style, ...rest } = attrs
  if (!rest.id && injectedId) rest.id = injectedId
  return rest
})

function onInput(event) {
  emit('update:modelValue', event.target.value)
}
</script>

<style scoped>
.field {
  display: block;
  width: 100%;
  background: var(--color-surface);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-sm);
  transition:
    border-color var(--transition),
    box-shadow var(--transition);
}

.field:hover:not(.field--disabled) {
  border-color: var(--color-text-faint);
}

.field:focus-within {
  border-color: var(--color-primary);
  box-shadow: var(--focus-ring);
}

.field--invalid {
  border-color: var(--color-danger);
}

.field--disabled {
  background: var(--color-surface-hover);
  cursor: not-allowed;
}

.field__control {
  display: block;
  width: 100%;
  border: 0;
  outline: none;
  background: transparent;
  color: inherit;
  padding: var(--space-2) var(--space-3);
  resize: vertical;
  min-height: 72px;
  line-height: var(--lh-base);
}

.field__control::placeholder {
  color: var(--color-text-faint);
}

.field__control:disabled {
  cursor: not-allowed;
}
</style>