<template>
  <section id="categories-section" class="cat" aria-labelledby="cat-heading">
    <div class="cat__head">
      <div>
        <h2 id="cat-heading" class="cat__title">Shop by category</h2>
        <p class="cat__subtitle">Jump straight to the aisle you came for.</p>
      </div>
      <button
        v-if="activeCategory"
        type="button"
        class="cat__clear"
        @click="selectCategory(null)"
      >
        Clear filter
        <AppIcon name="close" :size="14" />
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="cat__rail cat__rail--skeleton" aria-hidden="true">
      <div v-for="i in 4" :key="i" class="cat-skel">
        <span class="cat-skel__bar cat-skel__bar--lg" />
        <span class="cat-skel__bar" />
        <span class="cat-skel__bar cat-skel__bar--sm" />
      </div>
    </div>

    <!-- Categories -->
    <div
      v-else-if="categories.length"
      class="cat__rail"
      role="list"
      aria-label="Product categories"
    >
      <button
        type="button"
        class="cat-card"
        role="listitem"
        :class="{ 'cat-card--active': !activeCategory }"
        :aria-pressed="!activeCategory"
        @click="selectCategory(null)"
      >
        <span class="cat-card__top">
          <span class="cat-card__name">All products</span>
          <span class="cat-card__arrow" aria-hidden="true">
            <AppIcon name="arrowRight" :size="16" />
          </span>
        </span>
        <span class="cat-card__count tabular">{{ totalProducts }} items</span>
        <span class="cat-card__desc">The complete Meridian catalog</span>
      </button>

      <button
        v-for="category in categories"
        :key="category.value"
        type="button"
        class="cat-card"
        role="listitem"
        :class="{ 'cat-card--active': activeCategory === category.value }"
        :aria-pressed="activeCategory === category.value"
        @click="selectCategory(category.value)"
      >
        <span class="cat-card__top">
          <span class="cat-card__name">{{ formatCategory(category.value) }}</span>
          <span class="cat-card__arrow" aria-hidden="true">
            <AppIcon name="arrowRight" :size="16" />
          </span>
        </span>
        <span class="cat-card__count tabular">
          {{ category.count }} {{ category.count === 1 ? 'product' : 'products' }}
        </span>
        <span class="cat-card__desc">{{ describe(category.value) }}</span>
      </button>
    </div>

    <!-- Empty / error -->
    <div v-else class="cat__empty">
      <p class="cat__empty-title">Categories are unavailable right now.</p>
      <p class="cat__empty-text">You can still browse the full product collection below.</p>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../common/AppIcon.vue'

const props = defineProps({
  categories: { type: Array, default: () => [] },
  loading: Boolean,
})

const route = useRoute()
const router = useRouter()

const activeCategory = computed(() => String(route.query.category || ''))
const totalProducts = computed(() => props.categories.reduce((sum, c) => sum + (c.count || 0), 0))

/** Short merchandising line per category — falls back for unknown categories. */
const DESCRIPTIONS = {
  peripherals: 'Mice, keyboards, webcams & hubs',
  audio: 'Headphones, earbuds, mics & speakers',
  cables: 'USB-C, HDMI, ethernet & power',
  office: 'Desks, chairs, lighting & storage',
}

function describe(value) {
  return DESCRIPTIONS[value] || `${formatCategory(value)} essentials`
}

function formatCategory(value) {
  const raw = String(value || '')
  return raw.charAt(0).toUpperCase() + raw.slice(1)
}

function selectCategory(value) {
  const query = { ...route.query }
  if (value) query.category = value
  else delete query.category
  delete query.page
  router
    .replace({ query })
    .then(() => scrollToProducts())
    .catch(() => {})
}

/** Land on the product grid so the result of the selection is visible. */
function scrollToProducts() {
  const el = document.getElementById('products-section')
  if (!el) return
  const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches
  const top = el.getBoundingClientRect().top + window.scrollY - 96
  window.scrollTo({ top, behavior: reduced ? 'auto' : 'smooth' })
}
</script>

<style scoped>
.cat {
  width: 100%;
  margin-bottom: var(--space-8);
}

.cat__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.cat__title {
  margin: 0 0 var(--space-1);
  font-size: var(--text-2xl);
  line-height: 1.2;
  font-weight: var(--fw-bold);
  letter-spacing: -0.02em;
  color: var(--color-text);
}

.cat__subtitle {
  margin: 0;
  font-size: var(--text-base);
  color: var(--color-text-muted);
}

.cat__clear {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 36px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  white-space: nowrap;
  cursor: pointer;
  transition: border-color var(--transition), background-color var(--transition);
}

.cat__clear:hover {
  border-color: var(--color-text);
  background: var(--color-surface-hover);
}

/* ---------------- rail ---------------- */

.cat__rail {
  display: flex;
  gap: var(--space-3);
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  padding-bottom: var(--space-1);
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.cat__rail::-webkit-scrollbar {
  display: none;
}

/* ---------------- card ---------------- */

.cat-card {
  flex: 1 1 220px;
  min-width: 200px;
  max-width: 320px;
  scroll-snap-align: start;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-1);
  min-height: 128px;
  padding: var(--space-4) var(--space-5);
  text-align: left;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
  transition:
    border-color var(--transition),
    background-color var(--transition),
    box-shadow var(--transition),
    transform var(--transition);
}

.cat-card:hover {
  border-color: var(--color-text);
  box-shadow: var(--shadow-md);
  transform: translateY(-3px);
}

.cat-card:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.cat-card--active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-ink);
  box-shadow: var(--shadow-md);
}

.cat-card--active:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

.cat-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  width: 100%;
}

.cat-card__name {
  font-size: var(--text-md);
  font-weight: var(--fw-bold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  line-height: 1.2;
}

.cat-card__arrow {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex: none;
  border-radius: var(--radius-full);
  background: var(--color-surface-hover);
  color: var(--color-text);
  transition: transform var(--transition), background-color var(--transition);
}

.cat-card:hover .cat-card__arrow {
  transform: translateX(3px);
  background: var(--color-primary);
}

.cat-card--active .cat-card__arrow {
  background: var(--color-ink);
  color: var(--color-primary);
}

.cat-card__count {
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  color: var(--color-primary-hover);
}

.cat-card--active .cat-card__count {
  color: rgba(22, 22, 29, 0.75);
}

.cat-card__desc {
  font-size: var(--text-sm);
  line-height: 1.45;
  color: var(--color-text-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.cat-card--active .cat-card__desc {
  color: rgba(22, 22, 29, 0.72);
}

/* ---------------- skeleton ---------------- */

.cat-skel {
  flex: 1 1 220px;
  min-width: 200px;
  max-width: 320px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: var(--space-3);
  min-height: 128px;
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  animation: skeleton-pulse 1.2s ease-in-out infinite;
}

.cat-skel__bar {
  display: block;
  height: 12px;
  width: 55%;
  border-radius: var(--radius-sm);
  background: linear-gradient(
    90deg,
    var(--color-border) 25%,
    var(--color-surface-hover) 50%,
    var(--color-border) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

.cat-skel__bar--lg {
  width: 62%;
  height: 16px;
}

.cat-skel__bar--sm {
  width: 78%;
}

@keyframes skeleton-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.65;
  }
}

@keyframes shimmer {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}

/* ---------------- empty ---------------- */

.cat__empty {
  padding: var(--space-6);
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  text-align: center;
}

.cat__empty-title {
  margin: 0 0 var(--space-1);
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
}

.cat__empty-text {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

/* ---------------- responsive ---------------- */

@media (max-width: 640px) {
  .cat {
    margin-bottom: var(--space-6);
  }

  .cat__head {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-3);
    margin-bottom: var(--space-4);
  }

  .cat__title {
    font-size: var(--text-xl);
  }

  .cat-card,
  .cat-skel {
    width: 224px;
    min-height: 120px;
    padding: var(--space-4);
  }
}

@media (prefers-reduced-motion: reduce) {
  .cat-card,
  .cat-skel,
  .cat-skel__bar {
    transition: none;
    animation: none;
  }
}
</style>
