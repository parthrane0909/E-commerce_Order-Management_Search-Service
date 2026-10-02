<template>
  <div class="table-scroll">
    <table class="data-table catalog">
      <thead>
        <tr>
          <th>Image</th>
          <th>SKU</th>
          <th>Title</th>
          <th>Price</th>
          <th>Category</th>
          <th>Tags</th>
          <th>Variants</th>
          <th>Active</th>
          <th>Updated (UTC)</th>
          <th><span class="sr-only">Actions</span></th>
        </tr>
      </thead>

      <tbody v-if="loading">
        <tr v-for="index in 6" :key="index">
          <td v-for="col in 10" :key="col"><LoadingSkeleton variant="block" :height="14" /></td>
        </tr>
      </tbody>

      <tbody v-else>
        <tr v-for="product in items" :key="product.id">
          <td class="catalog__image-cell">
            <ProductThumb :product="product" size="sm" />
          </td>
          <td><code class="catalog__sku">{{ product.sku }}</code></td>
          <td>
            <div class="row-sm catalog__title-cell">
              <span class="medium truncate" :title="product.title">{{ product.title }}</span>
            </div>
          </td>
          <td class="tabular">{{ formatCurrency(product.price) }}</td>
          <td class="text-sm">{{ product.category }}</td>
          <td>
            <div class="catalog__tags">
              <template v-if="product.tags?.length">
                <span v-for="tag in product.tags.slice(0, 2)" :key="tag" class="tag-chip">
                  {{ tag }}
                </span>
                <span
                  v-if="product.tags.length > 2"
                  class="tag-chip tag-chip--more"
                  :title="product.tags.join(', ')"
                >
                  +{{ product.tags.length - 2 }}
                </span>
              </template>
              <span v-else class="text-xs faint">—</span>
            </div>
          </td>
          <td class="tabular">{{ product.variants?.length || 0 }}</td>
          <td>
            <AppBadge :tone="product.active ? 'success' : 'neutral'" size="sm">
              {{ product.active ? 'Active' : 'Inactive' }}
            </AppBadge>
          </td>
          <td class="text-sm muted tabular">{{ formatDateTime(product.updated_at) }}</td>
          <td>
            <div class="row-sm catalog__actions">
              <BaseButton size="sm" variant="ghost" icon="edit" @click="emit('edit', product)">
                Edit
              </BaseButton>
              <BaseButton
                size="sm"
                :variant="product.active ? 'ghost' : 'ghost'"
                :icon="product.active ? 'xCircle' : 'check'"
                @click="emit('toggle', product)"
              >
                {{ product.active ? 'Deactivate' : 'Activate' }}
              </BaseButton>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import LoadingSkeleton from '../common/LoadingSkeleton.vue'
import ProductThumb from '../common/ProductThumb.vue'
import AppBadge from '../common/AppBadge.vue'
import BaseButton from '../common/BaseButton.vue'
import { formatCurrency } from '../../utils/currency'
import { formatDateTime } from '../../utils/dates'

defineProps({
  items: { type: Array, default: () => [] },
  loading: Boolean,
})

const emit = defineEmits(['edit', 'toggle'])
</script>

<style scoped>
.catalog__sku {
  font-size: var(--text-xs);
  background: var(--color-surface-hover);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 2px 6px;
  white-space: nowrap;
}

.catalog__image-cell {
  width: 48px;
  padding: var(--space-2) var(--space-3);
}

.catalog__title-cell {
  max-width: 260px;
}

.catalog__tags {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  flex-wrap: wrap;
}

.tag-chip {
  font-size: 11px;
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--color-surface-hover);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  white-space: nowrap;
}

.tag-chip--more {
  background: var(--color-primary-soft);
  border-color: var(--color-primary-border);
  color: var(--color-primary-hover);
}

.catalog__actions {
  justify-content: flex-end;
  white-space: nowrap;
}
</style>