<template>
  <section class="category-section" aria-labelledby="category-heading">
    <div class="category-section__header">
      <h2 id="category-heading" class="category-section__title">
        Shop by Category
      </h2>
      <p class="category-section__subtitle">
        Browse our curated collections
      </p>
    </div>

    <div class="category-section__grid" v-if="categories.length">
      <RouterLink
        v-for="category in categories"
        :key="category.value"
        :to="categoryLink(category.value)"
        class="category-card"
        :class="{ 'category-card--active': isActiveCategory(category.value) }"
      >
        <div class="category-card__icon" :data-category="category.value">
          <AppIcon :name="categoryIcon(category.value)" :size="28" />
        </div>
        <h3 class="category-card__title">{{ formatCategory(category.value) }}</h3>
        <span class="category-card__count">{{ category.count }} products</span>
      </RouterLink>
    </div>

    <div v-else class="category-section__empty">
      <EmptyState icon="package" title="No categories found" />
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../common/AppIcon.vue'
import EmptyState from '../common/EmptyState.vue'

const route = useRoute()
const router = useRouter()

const props = defineProps({
  categories: { type: Array, default: () => [] },
})

const emit = defineEmits(['category-click'])

function formatCategory(value) {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function categoryIcon(category) {
  const icons = {
    peripherals: 'mouse',
    audio: 'headphones',
    cables: 'cable',
    office: 'package',
  }
  return icons[category] || 'package'
}

function categoryLink(category) {
  return { path: '/', query: { ...route.query, category, page: undefined } }
}

function isActiveCategory(category) {
  return route.query.category === category
}
</script>

<style scoped>
.category-section {
  max-width: var(--content-max);
  margin: 0 auto var(--space-10);
  padding: 0 var(--space-6);
}

.category-section__header {
  text-align: center;
  margin-bottom: var(--space-8);
}

.category-section__title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text);
  margin-bottom: var(--space-2);
}

.category-section__subtitle {
  font-size: var(--text-base);
  color: var(--text-muted);
}

.category-section__grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
}

.category-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-6) var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  text-decoration: none;
  color: var(--text);
  transition: box-shadow var(--transition), border-color var(--transition), transform var(--transition);
}

.category-card:hover {
  box-shadow: var(--shadow-2);
  border-color: var(--accent);
  transform: translateY(-2px);
  text-decoration: none;
  color: var(--text);
}

.category-card--active {
  border-color: var(--accent);
  box-shadow: var(--shadow-2);
}

.category-card__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: var(--accent-soft);
  border-radius: var(--radius);
  color: var(--accent-text);
}

.category-card__title {
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  text-align: center;
}

.category-card__count {
  font-size: var(--text-xs);
  color: var(--text-faint);
  text-align: center;
}

.category-section__empty {
  padding: var(--space-10) var(--space-4);
  text-align: center;
}

/* Responsive */
@media (max-width: 1100px) {
  .category-section__grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .category-section {
    padding: 0 var(--space-4);
  }

  .category-section__grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-3);
  }

  .category-card {
    padding: var(--space-4) var(--space-3);
  }

  .category-card__icon {
    width: 48px;
    height: 48px;
  }
}
</style>