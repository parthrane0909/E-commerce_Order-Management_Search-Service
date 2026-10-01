<template>
  <section class="filters" :class="{ 'filters--collapsed': collapsed }">
    <div class="filters__header" @click="collapsed = !collapsed">
      <span class="filters__title">
        <AppIcon name="sliders" :size="16" />
        Filters
      </span>
      <AppIcon :name="collapsed ? 'chevronDown' : 'chevronUp'" :size="16" class="filters__toggle" />
    </div>

    <Transition name="collapse">
      <div v-show="!collapsed" class="filters__content">
        <div class="filters__row">
          <BaseInput
            class="filters__search"
            :model-value="search"
            icon="search"
            placeholder="Search products…"
            aria-label="Search products"
            @update:model-value="emit('update:search', $event)"
          />

          <BaseSelect
            class="filters__select"
            :model-value="category"
            :options="categoryOptions"
            placeholder="All categories"
            aria-label="Filter by category"
            @update:model-value="emit('update:category', $event)"
          />

          <BaseSelect
            class="filters__select"
            :model-value="sort"
            :options="SORT_OPTIONS"
            aria-label="Sort products"
            @update:model-value="emit('update:sort', $event)"
          />
        </div>

        <div v-if="activeCount > 0" class="filters__actions">
          <BaseButton
            variant="ghost"
            icon="refresh"
            @click="emit('reset')"
          >
            Reset ({{ activeCount }})
          </BaseButton>
        </div>
      </div>
    </Transition>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import BaseInput from '../common/BaseInput.vue'
import BaseSelect from '../common/BaseSelect.vue'
import BaseButton from '../common/BaseButton.vue'
import AppIcon from '../common/AppIcon.vue'
import AppAlert from '../common/AppAlert.vue'
import LoadingSkeleton from '../common/LoadingSkeleton.vue'

const props = defineProps({
  search: { type: String, default: '' },
  category: { type: String, default: '' },
  sort: { type: String, default: 'newest' },
  selectedTags: { type: Array, default: () => [] },
  categoryFacets: { type: Array, default: () => [] },
  tagFacets: { type: Array, default: () => [] },
  tagsLoading: Boolean,
  tagsError: { type: String, default: '' },
})

const emit = defineEmits([
  'update:search',
  'update:category',
  'update:sort',
  'update:selectedTags',
  'reset',
])

const collapsed = ref(false)

const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest first' },
  { value: 'title_asc', label: 'Title A–Z' },
  { value: 'price_asc', label: 'Price: low to high' },
  { value: 'price_desc', label: 'Price: high to low' },
]

const categoryOptions = computed(() =>
  props.categoryFacets.map((facet) => ({
    value: facet.value,
    label: `${facet.value} (${facet.count})`,
  })),
)

const activeCount = computed(() => {
  let count = 0
  if (props.search.trim()) count += 1
  if (props.category) count += 1
  if (props.sort !== 'newest') count += 1
  return count
})
</script>

<style scoped>
.filters {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-1);
  overflow: hidden;
}

.filters__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-4);
  background: var(--surface-2);
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  user-select: none;
}

.filters__title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  color: var(--text);
}

.filters__toggle {
  color: var(--text-muted);
  transition: transform var(--transition);
}

.filters__content {
  padding: var(--space-4);
}

.filters__row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin-bottom: var(--space-4);
}

.filters__search {
  flex: 1 1 240px;
  min-width: 180px;
}

.filters__select {
  flex: 0 1 180px;
}

.filters__actions {
  padding-top: var(--space-3);
  border-top: 1px solid var(--border);
}

@media (max-width: 640px) {
  .filters__select {
    flex: 1 1 140px;
  }

  .filters__row {
    flex-direction: column;
    align-items: stretch;
  }

  .filters__search {
    min-width: 0;
  }

  .filters__select {
    width: 100%;
  }
}

/* Collapse animation */
.collapse-enter-active,
.collapse-leave-active {
  transition: max-height 0.25s ease, opacity 0.2s ease, padding 0.25s ease;
  overflow: hidden;
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.collapse-enter-to,
.collapse-leave-from {
  max-height: 1000px;
  opacity: 1;
}
</style>