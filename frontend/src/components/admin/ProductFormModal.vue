<template>
  <AppModal
    :open="open"
    :title="isEdit ? 'Edit product' : 'New product'"
    size="lg"
    :close-on-backdrop="!saving"
    @close="emit('close')"
  >
    <form class="product-form" @submit.prevent="submit">
      <AppAlert v-if="formError" tone="danger" dismissible @dismiss="formError = ''">
        {{ formError }}
      </AppAlert>

      <AppAlert v-if="isEdit" tone="info">
        Catalog changes affect future orders only — existing orders keep the snapshot recorded when
        they were placed.
      </AppAlert>

      <div class="product-form__grid">
        <FormField label="SKU" required :error="errors.sku" hint="2–64 chars: letters, numbers, - or _">
          <BaseInput
            v-model="form.sku"
            placeholder="ORG-001"
            :invalid="!!errors.sku"
            :disabled="saving"
          />
        </FormField>

        <FormField label="Category" required :error="errors.category">
          <BaseSelect
            v-model="form.category"
            :options="categoryOptions"
            placeholder="Select category"
            :invalid="!!errors.category"
            :disabled="saving"
          />
        </FormField>
      </div>

      <FormField label="Title" required :error="errors.title">
        <BaseInput
          v-model="form.title"
          placeholder="Desk Organizer Bamboo"
          :invalid="!!errors.title"
          :disabled="saving"
        />
      </FormField>

      <FormField label="Description" hint="Optional — shown under the product card">
        <BaseTextarea
          v-model="form.description"
          :rows="3"
          placeholder="Bamboo desk tidy with five compartments…"
          :disabled="saving"
        />
      </FormField>

      <div class="product-form__grid">
        <FormField label="Price (USD)" required :error="errors.price">
          <BaseInput
            v-model="form.price"
            type="number"
            min="0.01"
            step="0.01"
            placeholder="0.00"
            :invalid="!!errors.price"
            :disabled="saving"
          />
        </FormField>

        <FormField label="Visibility">
          <label class="switch">
            <input v-model="form.active" type="checkbox" :disabled="saving" />
            <span class="switch__track" aria-hidden="true">
              <span class="switch__thumb" />
            </span>
            <span class="switch__label">{{ form.active ? 'Active' : 'Inactive' }}</span>
          </label>
        </FormField>
      </div>

      <FormField label="Tags" hint="Press Enter or comma to add a chip">
        <TagsInput v-model="form.tags" :disabled="saving" />
      </FormField>

      <FormField label="Attributes" hint="Free-form key → value pairs, stored as JSON">
        <AttributesEditor v-model="form.attributes" />
      </FormField>

      <FormField label="Variants" :error="variantsError">
        <VariantsEditor v-model="form.variants" />
      </FormField>
    </form>

    <template #footer>
      <BaseButton variant="secondary" :disabled="saving" @click="emit('close')">Cancel</BaseButton>
      <BaseButton variant="primary" :loading="saving" @click="submit">
        {{ isEdit ? 'Save changes' : 'Create product' }}
      </BaseButton>
    </template>
  </AppModal>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import AppModal from '../common/AppModal.vue'
import AppAlert from '../common/AppAlert.vue'
import BaseButton from '../common/BaseButton.vue'
import BaseInput from '../common/BaseInput.vue'
import BaseSelect from '../common/BaseSelect.vue'
import BaseTextarea from '../common/BaseTextarea.vue'
import FormField from '../common/FormField.vue'
import TagsInput from './TagsInput.vue'
import AttributesEditor from './AttributesEditor.vue'
import VariantsEditor from './VariantsEditor.vue'
import { createProduct, updateProduct } from '../../api/products'
import { fieldErrorsFrom } from '../../api/client'
import {
  validateAttributeKeys,
  validateCategory,
  validatePrice,
  validateSku,
  validateTitle,
  validateVariants,
} from '../../utils/validation'

const props = defineProps({
  open: Boolean,
  product: { type: Object, default: null },
})

const emit = defineEmits(['close', 'saved'])

const BASE_CATEGORIES = [
  { value: 'peripherals', label: 'Peripherals' },
  { value: 'audio', label: 'Audio' },
  { value: 'cables', label: 'Cables' },
  { value: 'office', label: 'Office' },
]

const SERVER_FIELD_KEYS = [
  'sku',
  'title',
  'description',
  'price',
  'category',
  'tags',
  'attributes',
  'variants',
  'active',
]

const form = reactive({
  sku: '',
  title: '',
  description: '',
  price: '',
  category: '',
  tags: [],
  attributes: {},
  variants: [],
  active: true,
})

const errors = ref({})
const formError = ref('')
const saving = ref(false)

const isEdit = computed(() => Boolean(props.product))

const categoryOptions = computed(() => {
  const current = form.category
  const known = BASE_CATEGORIES.some((option) => option.value === current)
  if (current && !known) return [...BASE_CATEGORIES, { value: current, label: current }]
  return BASE_CATEGORIES
})

const variantsError = computed(() => {
  const rows = validateVariants(form.variants)
  return rows.some((row) => row.sku || row.stock) ? 'Fix the highlighted variant rows.' : ''
})

function loadForm() {
  const product = props.product
  form.sku = product?.sku ?? ''
  form.title = product?.title ?? ''
  form.description = product?.description ?? ''
  form.price = product ? String(product.price) : ''
  form.category = product?.category ?? ''
  form.tags = product?.tags ? [...product.tags] : []
  form.attributes = product?.attributes ? { ...product.attributes } : {}
  form.variants = (product?.variants ?? []).map((variant) => ({
    sku: variant.sku ?? '',
    color: variant.color ?? '',
    stock: variant.stock ?? 0,
  }))
  form.active = product ? product.active !== false : true
  errors.value = {}
  formError.value = ''
}

watch(
  () => props.open,
  (open) => {
    if (open) loadForm()
  },
)

function validate() {
  const next = {}
  const checks = {
    sku: validateSku(form.sku),
    title: validateTitle(form.title),
    price: validatePrice(form.price),
    category: validateCategory(form.category),
  }
  Object.entries(checks).forEach(([key, message]) => {
    if (message) next[key] = message
  })

  const attributeError = validateAttributeKeys(
    Object.keys(form.attributes).map((key) => ({ key })),
  )
  if (attributeError) formError.value = attributeError

  errors.value = next
  return Object.keys(next).length === 0 && !variantsError.value && !attributeError
}

async function submit() {
  if (saving.value) return
  if (!validate()) return

  saving.value = true
  formError.value = ''

  const payload = {
    sku: form.sku.trim(),
    title: form.title.trim(),
    description: form.description.trim(),
    price: Number(form.price),
    category: form.category.trim(),
    tags: [...form.tags],
    attributes: { ...form.attributes },
    variants: form.variants.map((variant) => ({
      sku: variant.sku.trim(),
      color: variant.color.trim() || null,
      stock: Number(variant.stock) || 0,
    })),
    active: form.active,
  }

  try {
    const saved = props.product
      ? await updateProduct(props.product.id, payload)
      : await createProduct(payload)
    emit('saved', saved, props.product ? 'updated' : 'created')
    emit('close')
  } catch (error) {
    const fieldErrors = fieldErrorsFrom(error)
    const known = Object.keys(fieldErrors).filter((key) => SERVER_FIELD_KEYS.includes(key))
    if (known.length) {
      errors.value = { ...errors.value, ...pick(fieldErrors, known) }
    } else {
      formError.value = error?.message || 'Could not save the product.'
    }
  } finally {
    saving.value = false
  }
}

function pick(source, keys) {
  return keys.reduce((acc, key) => {
    acc[key] = source[key]
    return acc
  }, {})
}
</script>

<style scoped>
.product-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.product-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.switch {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  padding: 7px 0;
}

.switch input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.switch__track {
  position: relative;
  width: 38px;
  height: 22px;
  border-radius: 999px;
  background: var(--border-strong);
  transition: background-color var(--transition);
  flex: none;
}

.switch__thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--surface);
  box-shadow: var(--shadow-1);
  transition: transform var(--transition);
}

.switch input:checked + .switch__track {
  background: var(--accent);
}

.switch input:checked + .switch__track .switch__thumb {
  transform: translateX(16px);
}

.switch input:focus-visible + .switch__track {
  box-shadow: var(--focus-ring);
}

.switch input:disabled + .switch__track {
  opacity: 0.6;
}

.switch__label {
  font-size: var(--text-base);
  color: var(--text-muted);
}

@media (max-width: 640px) {
  .product-form__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
