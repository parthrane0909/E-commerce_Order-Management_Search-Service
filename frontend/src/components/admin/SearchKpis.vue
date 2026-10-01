<template>
  <div class="kpis">
    <KpiCard
      label="Total revenue"
      :value="formatCurrency(aggregations?.revenue ?? 0)"
      tone="accent"
      :loading="loading"
    />
    <KpiCard
      label="Filtered orders"
      :value="formatNumber(total)"
      :loading="loading"
    />
    <KpiCard
      label="Pending"
      :value="formatNumber(counts.PENDING ?? 0)"
      tone="warning"
      :loading="loading"
    />
    <KpiCard
      label="Processing"
      :value="formatNumber(counts.PROCESSING ?? 0)"
      tone="info"
      :loading="loading"
    />
    <KpiCard
      label="Shipped"
      :value="formatNumber(counts.SHIPPED ?? 0)"
      tone="success"
      :loading="loading"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import KpiCard from '../common/KpiCard.vue'
import { formatCurrency, formatNumber } from '../../utils/currency'

const props = defineProps({
  aggregations: { type: Object, default: null },
  total: { type: Number, default: 0 },
  loading: Boolean,
})

const counts = computed(() => props.aggregations?.status_counts || {})
</script>

<style scoped>
.kpis {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--space-3);
}

@media (max-width: 1200px) {
  .kpis {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 420px) {
  .kpis {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>