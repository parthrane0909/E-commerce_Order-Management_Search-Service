<template>
  <div class="line-items">
    <div class="table-scroll">
      <table class="data-table line-items__table">
        <thead>
          <tr>
            <th class="line-items__num">#</th>
            <th>Product</th>
            <th class="line-items__num line-items__right">Qty</th>
            <th class="line-items__num line-items__right">Unit price</th>
            <th class="line-items__num line-items__right">Line total</th>
          </tr>
        </thead>

        <tbody v-if="loading">
          <tr v-for="index in 3" :key="index">
            <td colspan="5"><LoadingSkeleton variant="row" height="40" /></td>
          </tr>
        </tbody>

        <tbody v-else>
          <tr v-for="(row, index) in rows" :key="row.id">
            <td class="line-items__num muted">{{ index + 1 }}</td>
            <td>
              <div class="line-items__product">
                <ProductThumb :product="row" size="sm" />
                <div class="line-items__product-text">
                  <p class="line-items__title">{{ row.title }}</p>
                  <p class="text-xs muted">
                    <span v-if="row.sku">{{ row.sku }} · </span>
                    {{ row.category }}
                  </p>
                </div>
              </div>
              <AppBadge v-if="row.unavailable" tone="danger" size="sm" class="line-items__flag">
                No longer available
              </AppBadge>
            </td>
            <td class="line-items__num line-items__right tabular">{{ row.quantity }}</td>
            <td class="line-items__num line-items__right tabular">{{ formatCurrency(row.unitPrice) }}</td>
            <td class="line-items__num line-items__right tabular semibold">
              {{ formatCurrency(row.lineTotal) }}
            </td>
          </tr>
        </tbody>

        <tfoot>
          <tr>
            <td colspan="4" class="line-items__subtotal-label">Subtotal</td>
            <td class="line-items__num line-items__right tabular semibold">
              {{ formatCurrency(subtotal) }}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import LoadingSkeleton from '../common/LoadingSkeleton.vue'
import ProductThumb from '../common/ProductThumb.vue'
import AppBadge from '../common/AppBadge.vue'
import { formatCurrency } from '../../utils/currency'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  loading: Boolean,
})

const subtotal = computed(() =>
  props.rows.reduce((sum, row) => sum + (row.lineTotal || 0), 0),
)
</script>

<style scoped>
.line-items__table {
  min-width: 560px;
}

.line-items__table tfoot td {
  border-top: 1px solid var(--border);
  border-bottom: 0;
  background: var(--surface-2);
}

.line-items__subtotal-label {
  text-align: right;
  font-weight: var(--fw-medium);
  color: var(--text-muted);
}

.line-items__right {
  text-align: right;
}

.line-items__product {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.line-items__product-text {
  min-width: 0;
}

.line-items__title {
  font-weight: var(--fw-medium);
}

.line-items__flag {
  margin-top: var(--space-1);
}
</style>
