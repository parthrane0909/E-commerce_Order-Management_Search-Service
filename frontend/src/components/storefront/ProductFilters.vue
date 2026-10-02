<template>
  <section class="filters" :class="{ 'filters--open': !collapsed }">
    <button
      type="button"
      class="filters__toggle"
      @click="collapsed = !collapsed"
      :aria-expanded="!collapsed"
      aria-controls="filters-content"
    >
      <span class="filters__label">
        <AppIcon name="filter" :size="16" />
        Filters
      </span>
      <AppIcon :name="collapsed ? 'chevronDown' : 'chevronUp'" :size="16" class="filters__toggle-icon" />
    </button>

    <div
      id="filters-content"
      class="filters__content"
      v-show="!collapsed"
      role="region"
      aria-label="Product filters"
    >
      <Transition name="filter-fade">
        <div class="filters__inner">
          <div class="filters__group">
            <label for="category-select" class="filters__group-label">Category</label>
            <BaseSelect
              id="category-select"
              class="filters__select"
              :model-value="category"
              :options="categoryOptions"
              placeholder="All categories"
              aria-label="Filter by category"
              @update:model-value="emit('update:category', $event)"
            />
          </div>

          <div class="filters__group">
            <label for="sort-select" class="filters__group-label">Sort</label>
            <BaseSelect
              id="sort-select"
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
              size="sm"
              icon="refresh"
              @click="emit('reset')"
            >
              Clear ({{ activeCount }})
            </BaseButton>
          </div>
        </div>
      </Transition>
    </div>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue'
import BaseSelect from '../common/BaseSelect.vue'
import BaseButton from '../common/BaseButton.vue'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({
  category: { type: String, default: '' },
  sort: { type: String, default: 'newest' },
  selectedTags: { type: Array, default: () => [] },
  categoryFacets: { type: Array, default: () => [] },
  tagFacets: { type: Array, default: () => [] },
  tagsLoading: Boolean,
  tagsError: { type: String, default: '' },
})

const emit = defineEmits([
  'update:category',
  'update:sort',
  'update:selectedTags',
  'reset',
])

const collapsed = ref(true)

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
  if (props.category) count += 1
  if (props.sort !== 'newest') count += 1
  return count
})
</script>

<style scoped>
.filters {
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
}

.filters__toggle {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  cursor: pointer;
  transition:
    border-color var(--transition),
    background-color var(--transition),
    color var(--transition);
}

.filters__toggle:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
  color: var(--color-primary-hover);
}

.filters__toggle:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.filters__label {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
}

.filters__toggle-icon {
  color: var(--color-text-muted);
  transition: transform var(--transition);
}

.filters__content {
  overflow: hidden;
}

.filters__inner {
  padding: var(--space-5) 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  animation: filter-fade-in var(--duration-base) var(--transition) forwards;
}

@keyframes filter-fade-in {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.filters__group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.filters__group-label {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.filters__select {
  flex: 0 1 200px;
  min-width: 180px;
}

.filters__actions {
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 640px) {
  .filters {
    margin: 0 calc(var(--space-4) * -1);
    padding: 0 var(--space-4);
    border-top: 1px solid var(--color-border);
    border-bottom: 1px solid var(--color-border);
  }

  .filters__toggle {
    width: 100%;
    justify-content: space-between;
    border-radius: 0;
    border-left: none;
    border-right: none;
  }

  .filters__select {
    flex: 1 1 100%;
    width: 100%;
  }
}

/* Collapse animation */
.filter-fade-enter-active,
.filter-fade-leave-active {
  transition: opacity var(--duration-base) var(--transition), max-height var(--duration-base) var(--transition);
  overflow: hidden;
}

.filter-fade-enter-from,
.filter-fade-leave-to {
  opacity: 0;
  max-height: 0;
}

.filter-fade-enter-to,
.filter-fade-leave-from {
  max-height: 500px;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .filter-fade-enter-active,
  .filter-fade-leave-active {
    transition-duration: 0.01ms;
  }
}
</style>