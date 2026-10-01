<template>
  <div class="table-scroll">
    <table class="data-table results">
      <thead>
        <tr>
          <th>Order</th>
          <th>Customer</th>
          <th>Status</th>
          <th>Date</th>
          <th>Items</th>
          <th class="results__right">Total</th>
        </tr>
      </thead>

      <tbody v-if="loading">
        <tr v-for="index in 6" :key="index">
          <td colspan="6"><LoadingSkeleton variant="row" height="40" /></td>
        </tr>
      </tbody>

      <tbody v-else>
        <tr
          v-for="result in items"
          :key="result.order_id"
          class="results__row"
          tabindex="0"
          @click="emit('select', result.order_id)"
          @keydown.enter.prevent="emit('select', result.order_id)"
        >
          <td>
            <RouterLink
              class="results__link"
              :to="{ name: 'order-details', params: { id: result.order_id } }"
              @click.stop
            >
              {{ result.order_number }}
            </RouterLink>
          </td>
          <td>
            <p class="medium truncate">{{ result.customer?.name || '—' }}</p>
            <p class="text-xs muted truncate">{{ result.customer?.email || '' }}</p>
          </td>
          <td><StatusBadge :status="result.status" /></td>
          <td class="text-sm">{{ formatDateTime(result.order_date) }}</td>
          <td class="text-sm">
            <span class="muted">{{ result.items?.length || 0 }} items</span>
            <span v-if="firstItemTitle(result)" class="muted">
              ·
              <span class="truncate results__first-item" :title="firstItemTitle(result)">
                {{ firstItemTitle(result) }}
              </span>
            </span>
          </td>
          <td class="results__right tabular semibold">{{ formatCurrency(result.total_amount) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import LoadingSkeleton from '../common/LoadingSkeleton.vue'
import StatusBadge from '../common/StatusBadge.vue'
import { formatCurrency } from '../../utils/currency'
import { formatDateTime } from '../../utils/dates'

defineProps({
  items: { type: Array, default: () => [] },
  loading: Boolean,
})

const emit = defineEmits(['select'])

function firstItemTitle(result) {
  return result.items?.[0]?.title || ''
}
</script>

<style scoped>
.results__row {
  cursor: pointer;
  transition: background-color var(--transition);
}

.results__row:hover {
  background: var(--surface-2);
}

.results__row:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
}

.results__link {
  font-weight: var(--fw-medium);
}

.results__right {
  text-align: right;
}

.results__first-item {
  display: inline-block;
  max-width: 220px;
  vertical-align: bottom;
}
</style>
