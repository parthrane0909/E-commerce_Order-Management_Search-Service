<template>
  <section class="search-filters">
    <div class="search-filters__top">
      <BaseInput
        class="search-filters__query"
        :model-value="query"
        icon="search"
        placeholder="Search orders, customers or products…"
        aria-label="Search orders"
        @update:model-value="emit('update:query', $event)"
      />

      <AppBadge v-if="activeCount" tone="accent" class="search-filters__count">
        {{ activeCount }} {{ activeCount === 1 ? 'filter' : 'filters' }} active
      </AppBadge>

      <BaseButton
        variant="ghost"
        icon="refresh"
        :disabled="activeCount === 0"
        @click="emit('reset')"
      >
        Reset filters
      </BaseButton>
    </div>

    <div class="search-filters__grid">
      <div class="search-filters__field">
        <span class="search-filters__label">Status</span>
        <div class="search-filters__statuses">
          <label
            v-for="option in STATUS_OPTIONS"
            :key="option.value"
            class="status-chip"
            :class="{ 'status-chip--active': statuses.includes(option.value) }"
          >
            <input
              type="checkbox"
              class="sr-only"
              :checked="statuses.includes(option.value)"
              @change="toggleStatus(option.value)"
            />
            <span class="status-chip__box" aria-hidden="true">
              <AppIcon name="check" :size="12" />
            </span>
            {{ option.label }}
          </label>
        </div>
      </div>

      <FormField label="Date from">
        <BaseInput
          :model-value="dateFrom"
          type="date"
          @update:model-value="emit('update:dateFrom', $event)"
        />
      </FormField>

      <FormField label="Date to">
        <BaseInput
          :model-value="dateTo"
          type="date"
          @update:model-value="emit('update:dateTo', $event)"
        />
      </FormField>

      <FormField label="Min total" :hint="priceHint">
        <BaseInput
          :model-value="minPrice"
          type="number"
          min="0"
          step="0.01"
          placeholder="0.00"
          :invalid="!!priceHint"
          @update:model-value="emit('update:minPrice', $event)"
        />
      </FormField>

      <FormField label="Max total">
        <BaseInput
          :model-value="maxPrice"
          type="number"
          min="0"
          step="0.01"
          placeholder="1000.00"
          :invalid="!!priceHint"
          @update:model-value="emit('update:maxPrice', $event)"
        />
      </FormField>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import BaseInput from '../common/BaseInput.vue'
import BaseButton from '../common/BaseButton.vue'
import FormField from '../common/FormField.vue'
import AppIcon from '../common/AppIcon.vue'
import AppBadge from '../common/AppBadge.vue'
import { ORDER_STATUSES, statusOptions } from '../../utils/status'

const props = defineProps({
  query: { type: String, default: '' },
  statuses: { type: Array, default: () => [] },
  dateFrom: { type: String, default: '' },
  dateTo: { type: String, default: '' },
  minPrice: { type: String, default: '' },
  maxPrice: { type: String, default: '' },
  activeCount: { type: Number, default: 0 },
})

const emit = defineEmits([
  'update:query',
  'update:statuses',
  'update:dateFrom',
  'update:dateTo',
  'update:minPrice',
  'update:maxPrice',
  'reset',
])

const STATUS_OPTIONS = statusOptions()

const priceHint = computed(() => {
  const min = props.minPrice
  const max = props.maxPrice
  if (min === '' || max === '') return ''
  return Number(min) > Number(max) ? 'Minimum is greater than maximum.' : ''
})

function toggleStatus(status) {
  const next = props.statuses.includes(status)
    ? props.statuses.filter((value) => value !== status)
    : [...props.statuses, status]
  // Keep a stable PENDING, PROCESSING, SHIPPED ordering.
  next.sort((a, b) => ORDER_STATUSES.indexOf(a) - ORDER_STATUSES.indexOf(b))
  emit('update:statuses', next)
}
</script>

<style scoped>
.search-filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-1);
}

.search-filters__top {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.search-filters__query {
  flex: 1 1 320px;
}

.search-filters__count {
  flex: none;
}

.search-filters__grid {
  display: grid;
  grid-template-columns: 1.6fr repeat(4, minmax(0, 1fr));
  gap: var(--space-3);
  align-items: start;
  padding-top: var(--space-3);
  border-top: 1px dashed var(--border);
}

.search-filters__field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.search-filters__label {
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
}

.search-filters__statuses {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 6px 12px;
  border: 1px solid var(--border-strong);
  border-radius: 999px;
  background: var(--surface);
  color: var(--text-muted);
  font-size: var(--text-sm);
  cursor: pointer;
  user-select: none;
  transition:
    background-color var(--transition),
    border-color var(--transition),
    color var(--transition);
}

.status-chip:hover {
  border-color: var(--accent);
  color: var(--accent-text);
}

.status-chip:focus-within {
  box-shadow: var(--focus-ring);
}

.status-chip__box {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 15px;
  height: 15px;
  border: 1px solid var(--border-strong);
  border-radius: 4px;
  background: var(--surface);
  color: transparent;
  transition: background-color var(--transition), border-color var(--transition), color var(--transition);
}

.status-chip--active {
  background: var(--accent-soft);
  border-color: var(--accent);
  color: var(--accent-text);
  font-weight: var(--fw-medium);
}

.status-chip--active .status-chip__box {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--on-accent);
}

@media (max-width: 1100px) {
  .search-filters__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .search-filters__grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
