<template>
  <section class="product-grid">
    <div v-if="loading" class="product-grid__skeleton" aria-hidden="true">
      <div v-for="i in 8" :key="i" class="product-skeleton">
        <div class="product-skeleton__image" />
        <div class="product-skeleton__body">
          <div class="product-skeleton__line product-skeleton__line--short" />
          <div class="product-skeleton__line" />
          <div class="product-skeleton__line product-skeleton__line--short" />
          <div class="product-skeleton__line product-skeleton__line--short" />
          <div class="product-skeleton__btn" />
        </div>
      </div>
    </div>

    <div v-else-if="error" class="product-grid__error">
      <AppAlert tone="danger" title="Could not load products">
        {{ error }}
      </AppAlert>
      <BaseButton variant="secondary" icon="refresh" @click="emit('retry')">Retry</BaseButton>
    </div>

    <EmptyState
      v-else-if="!items.length"
      icon="search"
      title="No products match your filters"
      message="Try a different search term, category or tag combination."
    >
      <template #actions>
        <BaseButton variant="secondary" icon="refresh" @click="emit('clear')">
          Clear filters
        </BaseButton>
      </template>
    </EmptyState>

    <div v-else class="product-grid__items">
      <ProductCard
        v-for="product in items"
        :key="product.id"
        :product="product"
        @add="emit('add', $event)"
      />
    </div>
  </section>
</template>

<script setup>
import LoadingSkeleton from '../common/LoadingSkeleton.vue'
import EmptyState from '../common/EmptyState.vue'
import BaseButton from '../common/BaseButton.vue'
import ProductCard from './ProductCard.vue'
import AppAlert from '../common/AppAlert.vue'

defineProps({
  items: { type: Array, default: () => [] },
  loading: Boolean,
  error: { type: String, default: '' },
})

const emit = defineEmits(['add', 'clear', 'retry'])
</script>

<style scoped>
.product-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.product-grid__items {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-5);
}

.product-grid__error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  text-align: center;
}

.product-grid__error .alert {
  width: 100%;
  max-width: 400px;
}

/* Skeleton */
.product-grid__skeleton {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-5);
}

.product-skeleton {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  animation: skeleton-pulse var(--duration-slower) ease-in-out infinite;
}

.product-skeleton__image {
  aspect-ratio: 4 / 3;
  background: linear-gradient(90deg, var(--color-border) 25%, var(--color-surface-hover) 50%, var(--color-border) 75%);
  background-size: 200% 100%;
  animation: shimmer var(--duration-slower) ease-in-out infinite;
}

.product-skeleton__body {
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.product-skeleton__line {
  height: 12px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-border) 25%, var(--color-surface-hover) 50%, var(--color-border) 75%);
  background-size: 200% 100%;
  animation: shimmer var(--duration-slower) ease-in-out infinite;
}

.product-skeleton__line--short {
  width: 60%;
}

.product-skeleton__btn {
  height: 40px;
  width: 100%;
  border-radius: var(--radius);
  background: linear-gradient(90deg, var(--color-primary-soft) 25%, var(--color-primary-border) 50%, var(--color-primary-soft) 75%);
  background-size: 200% 100%;
  animation: shimmer var(--duration-slower) ease-in-out infinite;
  margin-top: auto;
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* Responsive */
@media (max-width: 1200px) {
  .product-grid__items,
  .product-grid__skeleton {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .product-grid__items,
  .product-grid__skeleton {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .product-grid__items,
  .product-grid__skeleton {
    grid-template-columns: 1fr;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .product-skeleton {
    animation: none;
  }
  .product-skeleton__image,
  .product-skeleton__line,
  .product-skeleton__btn {
    animation: none;
  }
}
</style>