<template>
  <div
    class="field"
    :class="[
      `field--${size}`,
      {
        'field--icon': !!icon,
        'field--invalid': invalid,
        'field--disabled': disabled,
      },
      attrs.class,
    ]"
    :style="attrs.style"
  >
    <AppIcon v-if="icon" :name="icon" :size="16" class="field__icon" />
    <input
      class="field__control"
      v-bind="controlBindings"
      :value="modelValue"
      :type="type"
      :placeholder="placeholder"
      :disabled="disabled || undefined"
      :aria-invalid="invalid ? 'true' : undefined"
      @input="onInput"
    />
  </div>
</template>

<script setup>
import { computed, inject, useAttrs } from 'vue'
import AppIcon from './AppIcon.vue'

defineOptions({ inheritAttrs: false })

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  disabled: Boolean,
  invalid: Boolean,
  icon: String,
  size: { type: String, default: 'md' },
})

const emit = defineEmits(['update:modelValue'])
const attrs = useAttrs()
const injectedId = inject('meridian.formFieldId', null)

// Everything except class/style goes to the input itself; class/style stay on
// the shell so parent utilities (width, flex, margin) apply where expected.
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
  display: flex;
  align-items: center;
  gap: var(--space-2);
  position: relative;
  width: 100%;
  background: var(--surface);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  transition:
    border-color var(--transition),
    box-shadow var(--transition),
    background-color var(--transition);
}

.field:hover:not(.field--disabled) {
  border-color: var(--text-faint);
}

.field:focus-within {
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}

.field--invalid {
  border-color: var(--danger);
}

.field--invalid:focus-within {
  box-shadow: 0 0 0 3px rgba(185, 28, 28, 0.28);
}

.field--disabled {
  background: var(--surface-2);
  color: var(--text-faint);
  cursor: not-allowed;
}

.field__icon {
  margin-left: var(--space-3);
  color: var(--text-faint);
}

.field__control {
  flex: 1 1 auto;
  min-width: 0;
  border: 0;
  outline: none;
  background: transparent;
  color: inherit;
  padding: 0 var(--space-3);
}

.field--icon .field__control {
  padding-left: 0;
}

.field--md .field__control {
  height: 36px;
}

.field--sm .field__control {
  height: 30px;
  font-size: var(--text-sm);
}

.field__control::placeholder {
  color: var(--text-faint);
}

.field__control:disabled {
  cursor: not-allowed;
}

/* Native date/number pickers keep their own chrome but inherit height. */
.field__control[type='date'],
.field__control[type='number'] {
  padding-right: var(--space-2);
}

.field__control[type='number'] {
  -moz-appearance: textfield;
  appearance: textfield;
}
</style>
