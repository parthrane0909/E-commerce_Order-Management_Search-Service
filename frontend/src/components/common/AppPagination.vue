<template>
  <nav class="pagination" :class="{ 'pagination--busy': loading }" aria-label="Pagination">
    <p class="pagination__summary">
      <span class="tabular">{{ formatNumber(total) }}</span>
      {{ itemLabel }}
      <span class="muted"> · page {{ page }} of {{ Math.max(pages, 1) }}</span>
    </p>

    <div class="pagination__controls">
      <BaseButton
        variant="secondary"
        size="sm"
        icon="chevronLeft"
        :disabled="loading || page <= 1"
        @click="goTo(page - 1)"
      >
        Prev
      </BaseButton>

      <div class="pagination__dots" aria-hidden="true">
        <span
          v-for="index in Math.min(pages, 7)"
          :key="index"
          class="pagination__dot"
          :class="{ 'pagination__dot--active': index === page }"
        />
      </div>

      <BaseButton
        variant="secondary"
        size="sm"
        icon="chevronRight"
        :disabled="loading || page >= pages"
        @click="goTo(page + 1)"
      >
        Next
      </BaseButton>
    </div>
  </nav>
</template>

<script setup>
import BaseButton from './BaseButton.vue'
import { formatNumber } from '../../utils/currency'

const props = defineProps({
  page: { type: Number, required: true },
  pages: { type: Number, default: 0 },
  total: { type: Number, default: 0 },
  loading: Boolean,
  itemLabel: { type: String, default: 'results' },
})

const emit = defineEmits(['update:page'])

function goTo(nextPage) {
  if (props.loading) return
  if (nextPage < 1 || nextPage > props.pages || nextPage === props.page) return
  emit('update:page', nextPage)
}
</script>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
  padding: var(--space-3) 0;
}

.pagination--busy {
  opacity: 0.6;
}

.pagination__summary {
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.pagination__controls {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.pagination__dots {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0 var(--space-1);
}

.pagination__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--border-strong);
  transition: background-color var(--transition), transform var(--transition);
}

.pagination__dot--active {
  background: var(--accent);
  transform: scale(1.3);
}

@media (max-width: 560px) {
  .pagination {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
  }

  .pagination__controls {
    justify-content: center;
  }

  .pagination__dots {
    display: none;
  }
}
</style>
