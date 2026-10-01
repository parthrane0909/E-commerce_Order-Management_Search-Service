<template>
  <section class="product-grid">
    <LoadingSkeleton v-if="loading" variant="card" :count="8" />

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
  gap: var(--space-4);
}

.product-grid__items {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.product-grid__error {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.product-grid__error .alert {
  width: 100%;
}

@media (max-width: 1100px) {
  .product-grid__items {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .product-grid__items {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .product-grid__items {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
