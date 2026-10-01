<template>
  <ul v-if="loading" class="result-cards" aria-hidden="true">
    <li v-for="index in 4" :key="index" class="result-card result-card--skeleton">
      <LoadingSkeleton variant="block" width="40%" height="16" />
      <LoadingSkeleton variant="block" width="60%" height="14" />
      <LoadingSkeleton variant="block" width="75%" height="14" />
      <LoadingSkeleton variant="block" width="30%" height="18" />
    </li>
  </ul>

  <ul v-else class="result-cards">
    <li
      v-for="result in items"
      :key="result.order_id"
      class="result-card"
      tabindex="0"
      role="link"
      @click="emit('select', result.order_id)"
      @keydown.enter.prevent="emit('select', result.order_id)"
    >
      <div class="result-card__top">
        <RouterLink
          class="result-card__number"
          :to="{ name: 'order-details', params: { id: result.order_id } }"
          @click.stop
        >
          {{ result.order_number }}
        </RouterLink>
        <StatusBadge :status="result.status" size="sm" />
      </div>

      <p class="result-card__customer medium truncate">{{ result.customer?.name || '—' }}</p>
      <p class="text-xs muted truncate">{{ result.customer?.email || '' }}</p>

      <p class="text-sm muted">
        {{ formatDateTime(result.order_date) }} ·
        {{ result.items?.length || 0 }} items
        <span v-if="result.items?.[0]?.title" class="truncate result-card__first">
          · “{{ result.items[0].title }}”
        </span>
      </p>

      <p class="result-card__total tabular">{{ formatCurrency(result.total_amount) }}</p>
    </li>
  </ul>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import StatusBadge from '../common/StatusBadge.vue'
import LoadingSkeleton from '../common/LoadingSkeleton.vue'
import { formatCurrency } from '../../utils/currency'
import { formatDateTime } from '../../utils/dates'

defineProps({
  items: { type: Array, default: () => [] },
  loading: Boolean,
})

const emit = defineEmits(['select'])
</script>

<style scoped>
.result-cards {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.result-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: border-color var(--transition), box-shadow var(--transition);
}

.result-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-1);
}

.result-card:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.result-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.result-card__number {
  font-weight: var(--fw-semibold);
}

.result-card__first {
  display: inline-block;
  max-width: 100%;
  vertical-align: bottom;
}

.result-card__total {
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
  margin-top: var(--space-1);
}

.result-card--skeleton {
  gap: var(--space-2);
  cursor: default;
}
</style>
