<template>
  <div
    class="field field--select"
    :class="[
      `field--${size}`,
      {
        'field--invalid': invalid,
        'field--disabled': disabled,
      },
      attrs.class,
    ]"
    :style="attrs.style"
  >
    <select
      class="field__control"
      v-bind="controlBindings"
      :value="modelValue"
      :disabled="disabled || undefined"
      :aria-invalid="invalid ? 'true' : undefined"
      @change="onChange"
    >
      <option v-if="placeholder" value="">{{ placeholder }}</option>
      <option v-for="option in normalizedOptions" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
    <AppIcon name="chevronDown" :size="16" class="field__chevron" />
  </div>
</template>

<script setup>
import { computed, inject, useAttrs } from 'vue'
import AppIcon from './AppIcon.vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  options: { type: Array, default: () => [] },
  placeholder: { type: String, default: '' },
  disabled: Boolean,
  invalid: Boolean,
  size: { type: String, default: 'md' },
})

const emit = defineEmits(['update:modelValue'])
const attrs = useAttrs()
const injectedId = inject('meridian.formFieldId', null)

const controlBindings = computed(() => {
  const { class: _class, style: _style, ...rest } = attrs
  if (!rest.id && injectedId) rest.id = injectedId
  return rest
})

const normalizedOptions = computed(() =>
  props.options.map((option) =>
    typeof option === 'object' && option !== null
      ? { value: option.value, label: option.label ?? String(option.value) }
      : { value: option, label: String(option) },
  ),
)

function onChange(event) {
  emit('update:modelValue', event.target.value)
}
</script>

<style scoped>
.field {
  display: flex;
  align-items: center;
  position: relative;
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
  color: var(--color-text-faint);
  cursor: not-allowed;
}

.field__control {
  flex: 1 1 auto;
  min-width: 0;
  width: 100%;
  border: 0;
  outline: none;
  background: transparent;
  color: inherit;
  padding: 0 var(--space-6) 0 var(--space-3);
  appearance: none;
  cursor: inherit;
}

.field--lg .field__control {
  height: 44px;
  font-size: var(--text-md);
}

.field--md .field__control {
  height: 38px;
}

.field--sm .field__control {
  height: 32px;
  font-size: var(--text-sm);
  padding-right: var(--space-5);
}

.field__control:disabled {
  cursor: not-allowed;
}

.field__chevron {
  position: absolute;
  right: var(--space-2);
  color: var(--color-text-muted);
  pointer-events: none;
}
</style>