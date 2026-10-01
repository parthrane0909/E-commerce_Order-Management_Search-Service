<template>
  <div class="tags-input" :class="{ 'tags-input--invalid': invalid }" @click="focusInput">
    <span v-for="(tag, index) in modelValue" :key="tag" class="tags-input__chip">
      {{ tag }}
      <button
        type="button"
        class="tags-input__remove"
        :aria-label="`Remove tag ${tag}`"
        :disabled="disabled"
        @click.stop="removeAt(index)"
      >
        <AppIcon name="close" :size="11" />
      </button>
    </span>

    <input
      ref="input"
      :id="fieldId || undefined"
      v-model="draft"
      class="tags-input__field"
      type="text"
      :placeholder="modelValue.length ? '' : placeholder"
      :aria-label="placeholder"
      :disabled="disabled"
      @keydown.enter.prevent="commit"
      @keydown="onKeydown"
      @blur="commit"
    />
  </div>
</template>

<script setup>
import { computed, inject, provide, ref } from 'vue'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Add a tag and press Enter' },
  invalid: Boolean,
  disabled: Boolean,
  max: { type: Number, default: 30 },
})

const emit = defineEmits(['update:modelValue'])

// The label of the enclosing FormField points at this input instead.
const fieldId = inject('meridian.formFieldId', null)
provide('meridian.formFieldId', null)

const draft = ref('')
const input = ref(null)

const tagSet = computed(() => new Set(props.modelValue))

function focusInput(event) {
  if (event.target.tagName !== 'INPUT') input.value?.focus()
}

function commit() {
  const tag = draft.value.trim().toLowerCase().replace(/^,+|,+$/g, '')
  if (!tag) {
    draft.value = ''
    return
  }
  if (tagSet.value.has(tag) || props.modelValue.length >= props.max) {
    draft.value = ''
    return
  }
  emit('update:modelValue', [...props.modelValue, tag])
  draft.value = ''
}

function removeAt(index) {
  const next = [...props.modelValue]
  next.splice(index, 1)
  emit('update:modelValue', next)
}

function onKeydown(event) {
  if (event.key === ',') {
    event.preventDefault()
    commit()
    return
  }
  if (event.key === 'Backspace' && !draft.value && props.modelValue.length) {
    removeAt(props.modelValue.length - 1)
  }
}
</script>

<style scoped>
.tags-input {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  min-height: 38px;
  padding: 6px var(--space-2);
  background: var(--surface);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  cursor: text;
  transition: border-color var(--transition), box-shadow var(--transition);
}

.tags-input:focus-within {
  border-color: var(--accent);
  box-shadow: var(--focus-ring);
}

.tags-input--invalid {
  border-color: var(--danger);
}

.tags-input__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 4px 3px 9px;
  border-radius: 999px;
  background: var(--accent-soft);
  border: 1px solid var(--accent-soft-border);
  color: var(--accent-text);
  font-size: var(--text-sm);
}

.tags-input__remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 17px;
  height: 17px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: inherit;
  cursor: pointer;
}

.tags-input__remove:hover {
  background: var(--accent-soft-border);
}

.tags-input__field {
  flex: 1 1 120px;
  min-width: 120px;
  border: 0;
  outline: none;
  background: transparent;
  height: 24px;
  font-size: var(--text-base);
}
</style>
