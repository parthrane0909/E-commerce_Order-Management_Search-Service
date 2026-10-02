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

      <!-- Image Section -->
      <FormField label="Product Image" hint="Optional — shown on storefront product cards">
        <div class="image-section">
          <div v-if="currentImageUrl" class="image-preview">
            <img
              :src="previewSrc"
              :alt="form.title || 'Product image'"
              class="image-preview__img"
              @error="imageError = 'This image could not be loaded. Try re-uploading it.'"
            />
            <div class="image-preview__actions">
              <BaseButton
                variant="secondary"
                size="sm"
                icon="upload"
                @click="triggerFileInput"
                :disabled="saving || uploadingImage"
              >
                Replace
              </BaseButton>
              <BaseButton
                variant="danger"
                size="sm"
                icon="trash"
                @click="removeImage"
                :disabled="saving || uploadingImage"
              >
                Remove
              </BaseButton>
            </div>
          </div>
          <div v-else class="image-upload">
            <label class="image-upload__label" @click="triggerFileInput">
              <AppIcon name="upload" :size="24" class="image-upload__icon" />
              <span class="image-upload__text">Click to upload image</span>
              <span class="image-upload__hint">JPEG, PNG, WebP, SVG · Max 5 MB</span>
            </label>
          </div>
          <!-- Rendered outside the preview branches so "Replace" always has a target. -->
          <input
            ref="fileInput"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/svg+xml"
            class="image-upload__input"
            @change="onFileSelected"
            :disabled="saving || uploadingImage"
            aria-label="Upload product image"
          />
          <div v-if="uploadingImage" class="image-uploading">
            <LoadingSkeleton variant="text" width="60%" />
            <span class="text-sm muted">Uploading image…</span>
          </div>
          <p v-if="imageError" class="form-field__error">{{ imageError }}</p>
        </div>
      </FormField>

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
import LoadingSkeleton from '../common/LoadingSkeleton.vue'
import AppIcon from '../common/AppIcon.vue'
import { createProduct, updateProduct, uploadProductImage, removeProductImage } from '../../api/products'
import { fieldErrorsFrom } from '../../api/client'
import { resolveImageUrl } from '../../utils/image'
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

// Image management state
const currentImageUrl = ref('')
const uploadingImage = ref(false)
const imageError = ref('')
const fileInput = ref(null)
/** `currentImageUrl` may be an API path, a blob URL or an absolute URL. */
const previewSrc = computed(() => resolveImageUrl(currentImageUrl.value))
const pendingImageUpload = ref(false) // Track if we need to upload image after product save

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
  currentImageUrl.value = product?.image_url || ''
  errors.value = {}
  formError.value = ''
  imageError.value = ''
  pendingImageUpload.value = false
}

watch(
  () => props.open,
  (open) => {
    if (open) loadForm()
  },
)

function triggerFileInput() {
  fileInput.value?.click()
}

async function onFileSelected(event) {
  const file = event.target?.files?.[0]
  if (!file) return

  imageError.value = ''
  uploadingImage.value = true

  try {
    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/svg+xml']
    if (!allowedTypes.includes(file.type)) {
      throw new Error('Unsupported image format. Please use JPEG, PNG, WebP, or SVG.')
    }

    // Validate file size (5 MB)
    const maxSize = 5 * 1024 * 1024
    if (file.size > maxSize) {
      throw new Error('File too large. Maximum size: 5 MB.')
    }

    // If editing existing product, upload immediately
    if (isEdit.value && props.product?.id) {
      const response = await uploadProductImage(props.product.id, file)
      currentImageUrl.value = response.image_url
    } else {
      // For new product, store file to upload after product creation
      pendingImageUpload.value = file
      currentImageUrl.value = URL.createObjectURL(file)
    }
  } catch (err) {
    imageError.value = err.message || 'Failed to upload image.'
    event.target.value = '' // Reset file input
  } finally {
    uploadingImage.value = false
  }
}

async function removeImage() {
  if (!isEdit.value || !props.product?.id) {
    // For new product, just clear the pending upload
    if (pendingImageUpload.value) {
      URL.revokeObjectURL(currentImageUrl.value)
      pendingImageUpload.value = false
      currentImageUrl.value = ''
    }
    return
  }

  imageError.value = ''
  uploadingImage.value = true

  try {
    const response = await removeProductImage(props.product.id)
    currentImageUrl.value = response.image_url || ''
  } catch (err) {
    imageError.value = err.message || 'Failed to remove image.'
  } finally {
    uploadingImage.value = false
  }
}

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
  imageError.value = ''

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
    let saved

    if (isEdit.value) {
      // For existing product, image is already uploaded if changed
      // But if we have a pending image upload (shouldn't happen for edit), handle it
      saved = await updateProduct(props.product.id, payload)
    } else {
      // Create product first
      saved = await createProduct(payload)

      // Then upload image if we have a pending file
      if (pendingImageUpload.value) {
        try {
          await uploadProductImage(saved.id, pendingImageUpload.value)
          // Refresh the product to get the image_url
          const refreshed = await updateProduct(saved.id, {}) // Just to trigger a fetch with image
          saved = refreshed
        } catch (imageErr) {
          // Product created but image upload failed - show warning but don't fail the whole operation
          imageError.value = `Product created but image upload failed: ${imageErr.message}`
        }
      }
    }

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
    pendingImageUpload.value = false
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
  height: 0.
}

.switch__track {
  position: relative;
  width: 38px;
  height: 22px;
  border-radius: 999px;
  background: var(--color-border-strong);
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
  background: var(--color-surface);
  box-shadow: var(--shadow-sm);
  transition: transform var(--transition);
}

.switch input:checked + .switch__track {
  background: var(--color-primary);
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
  color: var(--color-text-muted);
}

/* Image Section Styles */
.image-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.image-preview {
  position: relative;
  display: inline-flex;
  flex-direction: column;
  gap: var(--space-2);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  overflow: hidden;
  max-width: 320px;
}

.image-preview__img {
  width: 320px;
  height: 200px;
  object-fit: cover;
  display: block;
}

.image-preview__actions {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-3);
  border-top: 1px solid var(--color-border);
  background: var(--color-surface-hover);
}

.image-upload {
  border: 2px dashed var(--color-border-strong);
  border-radius: var(--radius);
  padding: var(--space-6) var(--space-4);
  text-align: center;
  cursor: pointer;
  transition: border-color var(--transition), background-color var(--transition);
}

.image-upload:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}

.image-upload__label {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  width: 100%;
}

.image-upload__icon {
  color: var(--color-primary);
  opacity: 0.8;
}

.image-upload__text {
  font-size: var(--text-base);
  font-weight: var(--fw-medium);
  color: var(--color-text);
}

.image-upload__hint {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.image-upload__input {
  display: none;
}

.image-uploading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4);
  text-align: center;
}

@media (max-width: 640px) {
  .product-form__grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .image-preview__img {
    width: 100%;
    height: 180px;
  }
}
</style>