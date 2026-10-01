<template>
  <ul class="catalog-cards">
    <li v-for="product in items" :key="product.id" class="catalog-card">
      <div class="catalog-card__head">
        <div class="row-sm">
          <ProductThumb :product="product" size="sm" />
          <div class="catalog-card__head-text">
            <p class="medium truncate" :title="product.title">{{ product.title }}</p>
            <code class="text-xs muted">{{ product.sku }}</code>
          </div>
        </div>
        <AppBadge :tone="product.active ? 'success' : 'neutral'" size="sm">
          {{ product.active ? 'Active' : 'Inactive' }}
        </AppBadge>
      </div>

      <dl class="catalog-card__facts">
        <div>
          <dt>Price</dt>
          <dd class="tabular">{{ formatCurrency(product.price) }}</dd>
        </div>
        <div>
          <dt>Category</dt>
          <dd>{{ product.category }}</dd>
        </div>
        <div>
          <dt>Variants</dt>
          <dd class="tabular">{{ product.variants?.length || 0 }}</dd>
        </div>
        <div>
          <dt>Updated</dt>
          <dd class="tabular">{{ formatDateTime(product.updated_at) }}</dd>
        </div>
      </dl>

      <div v-if="product.tags?.length" class="catalog-card__tags">
        <span v-for="tag in product.tags.slice(0, 3)" :key="tag" class="tag-chip">{{ tag }}</span>
        <span v-if="product.tags.length > 3" class="tag-chip tag-chip--more">
          +{{ product.tags.length - 3 }}
        </span>
      </div>

      <div class="catalog-card__actions">
        <BaseButton size="sm" variant="secondary" icon="edit" @click="emit('edit', product)">
          Edit
        </BaseButton>
        <BaseButton
          size="sm"
          variant="ghost"
          :icon="product.active ? 'xCircle' : 'check'"
          @click="emit('toggle', product)"
        >
          {{ product.active ? 'Deactivate' : 'Activate' }}
        </BaseButton>
      </div>
    </li>
  </ul>
</template>

<script setup>
import ProductThumb from '../common/ProductThumb.vue'
import AppBadge from '../common/AppBadge.vue'
import BaseButton from '../common/BaseButton.vue'
import { formatCurrency } from '../../utils/currency'
import { formatDateTime } from '../../utils/dates'

defineProps({
  items: { type: Array, default: () => [] },
})

const emit = defineEmits(['edit', 'toggle'])
</script>

<style scoped>
.catalog-cards {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.catalog-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.catalog-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-2);
}

.catalog-card__head-text {
  min-width: 0;
}

.catalog-card__facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-2);
  margin: 0;
  padding-top: var(--space-3);
  border-top: 1px dashed var(--border);
}

.catalog-card__facts dt {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-faint);
}

.catalog-card__facts dd {
  margin: 0;
  font-size: var(--text-sm);
}

.catalog-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
}

.tag-chip {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--text-muted);
}

.tag-chip--more {
  background: var(--accent-soft);
  border-color: var(--accent-soft-border);
  color: var(--accent-text);
}

.catalog-card__actions {
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
  border-top: 1px solid var(--border);
  padding-top: var(--space-3);
}
</style>
