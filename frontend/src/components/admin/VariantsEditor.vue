<template>
  <div class="variants">
    <div v-if="!rows.length" class="variants__empty text-sm muted">
      No variants — add one if this product comes in different colours or stock units.
    </div>

    <div v-for="(row, index) in rows" :key="index" class="variants__row">
      <div class="variants__cell">
        <BaseInput
          :id="index === 0 ? fieldId || undefined : undefined"
          v-model="row.sku"
          placeholder="Variant SKU"
          size="sm"
          :invalid="!!errors[index]?.sku"
          @update:model-value="onChange"
        />
        <span v-if="errors[index]?.sku" class="variants__error">{{ errors[index].sku }}</span>
      </div>

      <div class="variants__cell">
        <BaseInput
          v-model="row.color"
          placeholder="Colour (optional)"
          size="sm"
          @update:model-value="onChange"
        />
      </div>

      <div class="variants__cell variants__cell--stock">
        <BaseInput
          v-model="row.stock"
          type="number"
          min="0"
          step="1"
          placeholder="Stock"
          size="sm"
          :invalid="!!errors[index]?.stock"
          @update:model-value="onChange"
        />
        <span v-if="errors[index]?.stock" class="variants__error">{{ errors[index].stock }}</span>
      </div>

      <button
        type="button"
        class="variants__remove"
        :aria-label="`Remove variant ${index + 1}`"
        @click="removeRow(index)"
      >
        <AppIcon name="trash" :size="15" />
      </button>
    </div>

    <BaseButton size="sm" variant="secondary" icon="plus" class="variants__add" @click="addRow">
      Add variant
    </BaseButton>
  </div>
</template>

<script setup>
import { computed, inject, provide, ref, watch } from 'vue'
import BaseInput from '../common/BaseInput.vue'
import BaseButton from '../common/BaseButton.vue'
import AppIcon from '../common/AppIcon.vue'
import { validateVariant } from '../../utils/validation'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue'])

const fieldId = inject('meridian.formFieldId', null)
provide('meridian.formFieldId', null)

function toRows(value) {
  return (value || []).map((variant) => ({
    sku: String(variant.sku ?? ''),
    color: String(variant.color ?? ''),
    stock: variant.stock === '' || variant.stock === null || variant.stock === undefined
      ? ''
      : String(variant.stock),
  }))
}

function rowsKey(list) {
  return JSON.stringify(list)
}

const rows = ref(toRows(props.modelValue))

watch(
  () => props.modelValue,
  (value) => {
    const next = toRows(value)
    if (rowsKey(next) !== rowsKey(rows.value)) rows.value = next
  },
)

const errors = computed(() => rows.value.map((row) => validateVariant(row)))

function onChange() {
  emit(
    'update:modelValue',
    rows.value.map((row) => ({
      sku: row.sku.trim(),
      color: row.color.trim(),
      stock: row.stock,
    })),
  )
}

function addRow() {
  rows.value = [...rows.value, { sku: '', color: '', stock: '0' }]
  onChange()
}

function removeRow(index) {
  const next = [...rows.value]
  next.splice(index, 1)
  rows.value = next
  onChange()
}
</script>

<style scoped>
.variants {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.variants__empty {
  padding: var(--space-3);
  background: var(--surface-2);
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius-sm);
}

.variants__row {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr) minmax(0, 0.7fr) 32px;
  gap: var(--space-2);
  align-items: start;
}

.variants__cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.variants__error {
  font-size: var(--text-xs);
  color: var(--danger);
}

.variants__remove {
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

.variants__remove:hover {
  background: var(--danger-soft);
  border-color: var(--danger-border);
  color: var(--danger);
}

.variants__add {
  align-self: flex-start;
}

@media (max-width: 640px) {
  .variants__row {
    grid-template-columns: minmax(0, 1fr) 32px;
    padding-bottom: var(--space-2);
    border-bottom: 1px dashed var(--border);
  }

  .variants__cell--stock {
    grid-column: 1 / 2;
  }
}
</style>
