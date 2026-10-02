<template>
  <article class="product-card" :class="{ 'product-card--added': state === 'added' }">
    <div class="product-card__media">
      <ProductThumb :product="product" size="md" class="product-card__image" />
      <button
        type="button"
        class="product-card__wish"
        :class="{ 'product-card__wish--on': wished }"
        :aria-pressed="wished"
        :aria-label="wished ? `Remove ${product.title} from wishlist` : `Save ${product.title} to wishlist`"
        @click.stop="toggleWishlist"
      >
        <AppIcon name="heart" :size="17" />
      </button>
    </div>

    <div class="product-card__body">
      <p class="product-card__category">{{ formatCategory(product.category) }}</p>

      <h3 class="product-card__title" :title="product.title">{{ product.title }}</h3>

      <p class="product-card__desc">{{ description }}</p>

      <div class="product-card__price-row">
        <span class="product-card__price tabular">{{ formatCurrency(product.price) }}</span>
        <span v-if="product.tags && product.tags.length" class="product-card__tag">
          #{{ product.tags[0] }}
        </span>
      </div>

      <BaseButton
        class="product-card__cta"
        :variant="state === 'added' ? 'secondary' : 'primary'"
        :disabled="state === 'added'"
        @click="onAdd"
      >
        <svg
          v-if="state === 'added'"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.2"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M5 12.5l4.5 4.5L19 7" />
        </svg>
        {{ state === 'added' ? 'Added to cart' : 'Add to cart' }}
      </BaseButton>
    </div>
  </article>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import BaseButton from '../common/BaseButton.vue'
import AppIcon from '../common/AppIcon.vue'
import ProductThumb from '../common/ProductThumb.vue'
import { formatCurrency } from '../../utils/currency'

const props = defineProps({
  product: { type: Object, required: true },
})

const emit = defineEmits(['add'])

const RESET_AFTER = 1400

const state = ref('idle')
const wished = ref(false)
let timer = null

const description = computed(() => {
  const text = String(props.product.description || '').trim()
  return text || 'A Meridian workspace essential, in stock and ready to ship.'
})

function formatCategory(value) {
  const raw = String(value || '')
  return raw.charAt(0).toUpperCase() + raw.slice(1)
}

function onAdd() {
  if (state.value === 'added') return
  state.value = 'added'
  emit('add', props.product)
  clearTimeout(timer)
  timer = setTimeout(() => {
    state.value = 'idle'
  }, RESET_AFTER)
}

function toggleWishlist() {
  wished.value = !wished.value
}

onBeforeUnmount(() => clearTimeout(timer))
</script>

<style scoped>
.product-card {
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition:
    box-shadow var(--transition),
    border-color var(--transition),
    transform var(--transition);
}

.product-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: var(--shadow-lg);
  transform: translateY(-4px);
}

.product-card__media {
  position: relative;
  width: 100%;
  background: var(--color-bg);
  overflow: hidden;
}

.product-card__image {
  width: 100%;
}

.product-card__media :deep(.thumb) {
  width: 100%;
  aspect-ratio: 4 / 3;
}

.product-card__media :deep(.thumb__image) {
  transition: transform 400ms cubic-bezier(0.22, 1, 0.36, 1);
}

.product-card:hover .product-card__media :deep(.thumb__image) {
  transform: scale(1.05);
}

.product-card__wish {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.94);
  color: var(--color-text-muted);
  cursor: pointer;
  transition:
    background-color var(--transition),
    color var(--transition),
    border-color var(--transition),
    transform var(--transition),
    opacity var(--transition);
}

.product-card__wish:hover {
  border-color: var(--color-primary);
  color: var(--color-primary-hover);
  transform: scale(1.08);
}

.product-card__wish--on {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-ink);
}

.product-card__wish--on :deep(.app-icon) {
  fill: currentColor;
}

/* ---------------- body ---------------- */

.product-card__body {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  min-width: 0;
  padding: var(--space-4);
  gap: var(--space-2);
}

.product-card__category {
  margin: 0;
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-primary-hover);
}

.product-card__title {
  margin: 0;
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
  line-height: 1.35;
  letter-spacing: -0.01em;
  color: var(--color-text);
  min-height: 2.7em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  overflow-wrap: anywhere;
}

.product-card__desc {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.5;
  color: var(--color-text-muted);
  min-height: 3em;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-card__price-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-top: auto;
  padding-top: var(--space-3);
}

.product-card__price {
  font-size: var(--text-xl);
  font-weight: var(--fw-bold);
  letter-spacing: -0.02em;
  color: var(--color-text);
}

.product-card__tag {
  font-size: var(--text-xs);
  color: var(--color-text-faint);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 45%;
}

.product-card__cta {
  width: 100%;
  height: 40px;
}

.product-card--added .product-card__cta {
  background: var(--color-success);
  border-color: var(--color-success);
  color: #fff;
}

/* ---------------- responsive ---------------- */

/* Line reservations stay in place at every breakpoint so every card in the
   grid has exactly the same height (the clamp does the truncating). */

@media (prefers-reduced-motion: reduce) {
  .product-card,
  .product-card__wish {
    transition: none;
  }
}
</style>
