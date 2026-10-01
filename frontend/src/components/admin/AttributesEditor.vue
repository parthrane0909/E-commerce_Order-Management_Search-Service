<template>
  <div class="attributes">
    <div v-if="!rows.length" class="attributes__empty text-sm muted">
      No attributes yet — add a key/value pair such as
      <code>material</code> → <code>bamboo</code>.
    </div>

    <div v-for="(row, index) in rows" :key="index" class="attributes__row">
      <BaseInput
        :id="index === 0 ? fieldId || undefined : undefined"
        v-model="row.key"
        placeholder="key"
        size="sm"
        :invalid="!!duplicateError"
        @update:model-value="onChange"
      />
      <BaseInput
        v-model="row.value"
        placeholder="value"
        size="sm"
        @update:model-value="onChange"
      />
      <button
        type="button"
        class="attributes__remove"
        :aria-label="`Remove attribute ${row.key || index + 1}`"
        @click="removeRow(index)"
      >
        <AppIcon name="trash" :size="15" />
      </button>
    </div>

    <div class="attributes__footer">
      <BaseButton size="sm" variant="secondary" icon="plus" @click="addRow">
        Add attribute
      </BaseButton>
      <code class="attributes__preview" :title="preview">{{ preview }}</code>
    </div>

    <p v-if="duplicateError" class="attributes__error" role="alert">
      <AppIcon name="warning" :size="13" />
      {{ duplicateError }}
    </p>
  </div>
</template>

<script setup>
import { computed, inject, provide, ref, watch } from 'vue'
import BaseInput from '../common/BaseInput.vue'
import BaseButton from '../common/BaseButton.vue'
import AppIcon from '../common/AppIcon.vue'
import { coerceAttributeValue, validateAttributeKeys } from '../../utils/validation'

const props = defineProps({
  modelValue: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update:modelValue'])

const fieldId = inject('meridian.formFieldId', null)
provide('meridian.formFieldId', null)

function objectToRows(value) {
  return Object.entries(value || {}).map(([key, raw]) => ({
    key,
    value: typeof raw === 'object' && raw !== null ? JSON.stringify(raw) : String(raw),
  }))
}

function rowsKey(list) {
  return JSON.stringify(list)
}

const rows = ref(objectToRows(props.modelValue))

watch(
  () => props.modelValue,
  (value) => {
    const next = objectToRows(value)
    if (rowsKey(next) !== rowsKey(rows.value)) rows.value = next
  },
)

const duplicateError = computed(() => validateAttributeKeys(rows.value))

const preview = computed(() => {
  const out = {}
  rows.value.forEach((row) => {
    const key = row.key.trim()
    if (key) out[key] = coerceAttributeValue(row.value)
  })
  return JSON.stringify(out)
})

function onChange() {
  const out = {}
  rows.value.forEach((row) => {
    const key = row.key.trim()
    if (key) out[key] = coerceAttributeValue(row.value)
  })
  emit('update:modelValue', out)
}

function addRow() {
  rows.value = [...rows.value, { key: '', value: '' }]
}

function removeRow(index) {
  const next = [...rows.value]
  next.splice(index, 1)
  rows.value = next
  onChange()
}
</script>

<style scoped>
.attributes {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.attributes__empty {
  padding: var(--space-3);
  background: var(--surface-2);
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-sm);
}

.attributes__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 32px;
  gap: var(--space-2);
  align-items: center;
}

.attributes__remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 30px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text-faint);
  cursor: pointer;
  transition: background-color var(--transition), color var(--transition), border-color var(--transition);
}

.attributes__remove:hover {
  background: var(--danger-soft);
  border-color: var(--danger-border);
  color: var(--danger);
}

.attributes__footer {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.attributes__preview {
  flex: 1 1 200px;
  min-width: 0;
  padding: 6px var(--space-2);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: var(--text-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attributes__error {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-sm);
  color: var(--danger);
}
</style>
