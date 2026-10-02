<template>
  <div class="storefront-view">
    <HeroSection class="reveal reveal--1" />

    <CategorySection
      class="reveal reveal--2"
      :categories="facets.categories"
      :loading="facetsLoading && !facets.categories.length"
    />

    <TagMarquee
      v-if="facets.tags.length"
      class="reveal reveal--3"
      :tags="facets.tags"
      :clickable="true"
    />

    <!-- Product collection -->
    <section
      id="products-section"
      class="collection reveal reveal--4"
      aria-labelledby="collection-heading"
    >
      <header class="collection__head">
        <div class="collection__titles">
          <p v-if="searchTerm" class="collection__eyebrow">Search results</p>
          <h2 id="collection-heading" class="collection__title">
            <template v-if="searchTerm">
              “{{ searchTerm }}”
            </template>
            <template v-else-if="category">
              {{ prettyCategory(category) }}
            </template>
            <template v-else>
              The full collection
            </template>
          </h2>
          <p class="collection__meta">
            <template v-if="loading">Loading products…</template>
            <template v-else>
              <span class="collection__count tabular">{{ products.total }}</span>
              {{ products.total === 1 ? 'product' : 'products' }}
              <template v-if="searchTerm"> matching your search</template>
              <template v-else-if="category"> in {{ prettyCategory(category) }}</template>
            </template>
          </p>
        </div>

        <div class="collection__tools">
          <div v-if="searchTerm || category || sort !== 'newest'" class="collection__chips">
            <button v-if="searchTerm" type="button" class="chip" @click="clearQuery('q')">
              “{{ searchTerm }}”
              <AppIcon name="close" :size="13" />
            </button>
            <button v-if="category" type="button" class="chip" @click="clearQuery('category')">
              {{ prettyCategory(category) }}
              <AppIcon name="close" :size="13" />
            </button>
            <button
              v-if="sort !== 'newest'"
              type="button"
              class="chip"
              @click="onSortChange('newest')"
            >
              Sorted
              <AppIcon name="close" :size="13" />
            </button>
          </div>

          <ProductFilters
            :category="category"
            :sort="sort"
            :category-facets="facets.categories"
            @update:category="onCategoryChange"
            @update:sort="onSortChange"
            @reset="resetFilters"
          />
        </div>
      </header>

      <ProductGrid
        :items="products.items"
        :loading="loading"
        :error="error"
        @add="addToCart"
        @clear="resetFilters"
        @retry="load"
      />

      <AppPagination
        v-if="products.pages > 1"
        :page="page"
        :pages="products.pages"
        :total="products.total"
        :loading="loading"
        item-label="products"
        @update:page="setPage"
      />
    </section>

    <!-- Promotional band -->
    <section class="promo reveal reveal--5" aria-label="Why shop at Meridian">
      <article v-for="item in promos" :key="item.title" class="promo__item">
        <span class="promo__icon" aria-hidden="true">
          <AppIcon :name="item.icon" :size="22" />
        </span>
        <div>
          <h3 class="promo__title">{{ item.title }}</h3>
          <p class="promo__text">{{ item.text }}</p>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/common/AppIcon.vue'
import ProductFilters from '../components/storefront/ProductFilters.vue'
import ProductGrid from '../components/storefront/ProductGrid.vue'
import AppPagination from '../components/common/AppPagination.vue'
import HeroSection from '../components/storefront/HeroSection.vue'
import CategorySection from '../components/storefront/CategorySection.vue'
import TagMarquee from '../components/storefront/TagMarquee.vue'
import { listProducts, getProductFacets } from '../api/products'
import { useCartStore } from '../stores/cart'
import { useToastStore } from '../stores/toast'

const route = useRoute()
const router = useRouter()
const cart = useCartStore()
const toast = useToastStore()

const PAGE_SIZE = 12

const promos = [
  { icon: 'truck', title: 'Free shipping', text: 'On every order over ₹5,000' },
  { icon: 'undo', title: '30-day returns', text: 'Changed your mind? Send it back' },
  { icon: 'shield', title: 'Secure checkout', text: 'JWT-protected payments & orders' },
  { icon: 'box', title: 'Fast dispatch', text: 'Packed within one working day' },
]

function parseIntQuery(value) {
  const parsed = parseInt(String(value || ''), 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 1
}

// URL-driven filter state — single source of truth
const category = ref(String(route.query.category || ''))
const sort = ref(String(route.query.sort || 'newest'))
const page = ref(parseIntQuery(route.query.page))

const facets = ref({ categories: [], tags: [] })
const facetsLoading = ref(false)
const facetsError = ref('')

const products = ref({ items: [], total: 0, pages: 0, page: 1, limit: PAGE_SIZE })
const loading = ref(false)
const error = ref('')
let requestId = 0
let inFlightKey = ''

const searchTerm = computed(() => String(route.query.q || '').trim())

const routeCategory = computed(() => String(route.query.category || ''))
const routeSort = computed(() => String(route.query.sort || 'newest'))
const routePage = computed(() => parseIntQuery(route.query.page))

function prettyCategory(value) {
  const raw = String(value || '')
  return raw.charAt(0).toUpperCase() + raw.slice(1)
}

function pushQuery(patch) {
  const query = { ...route.query }
  Object.entries(patch).forEach(([key, value]) => {
    if (value === undefined || value === '' || value === null) delete query[key]
    else query[key] = String(value)
  })
  router.replace({ query }).catch(() => {})
}

/* ---------------- route -> local sync ---------------- */

watch(routeCategory, (value) => {
  if (value !== category.value) category.value = value
})

watch(routeSort, (value) => {
  if (value !== sort.value) sort.value = value
})

watch(routePage, (value) => {
  if (value !== page.value) page.value = value
})

/* ---------------- local controls ---------------- */

function onCategoryChange(value) {
  category.value = value
  pushQuery({ category: value || undefined, page: undefined })
  scrollToCollection()
}

function onSortChange(value) {
  sort.value = value
  pushQuery({ sort: value === 'newest' ? undefined : value, page: undefined })
}

function clearQuery(key) {
  if (key === 'q') {
    pushQuery({ q: undefined, page: undefined })
    return
  }
  if (key === 'category') {
    category.value = ''
    pushQuery({ category: undefined, page: undefined })
  }
}

function setPage(nextPage) {
  page.value = nextPage
  pushQuery({ page: nextPage > 1 ? nextPage : undefined })
  scrollToCollection()
}

function resetFilters() {
  category.value = ''
  sort.value = 'newest'
  router.replace({ query: {} }).catch(() => {})
  // When the query was already empty this replace is a duplicate navigation,
  // so no watcher fires — nudge a reload (empty-catalog edge case). Overlapping
  // watcher loads are folded together by the in-flight guard in load().
  if (page.value === 1) load()
}

function scrollToCollection() {
  const el = document.querySelector('#products-section')
  if (!el) return
  const top = el.getBoundingClientRect().top + window.scrollY - 96
  const behavior =
    window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ? 'auto' : 'smooth'
  window.scrollTo({ top, behavior })
}

/* ---------------- fetching ---------------- */

async function load() {
  const params = {
    page: page.value,
    limit: PAGE_SIZE,
    sort: sort.value,
    visibility: 'active',
  }
  const term = route.query.q?.trim()
  if (term) params.q = term
  if (category.value) params.category = category.value

  // Route sync and the filter watchers can both request the same fetch in one
  // tick (e.g. "Reset filters") — share the request already in flight.
  const key = JSON.stringify(params)
  if (loading.value && key === inFlightKey) return
  inFlightKey = key

  const id = (requestId += 1)
  loading.value = true
  error.value = ''
  try {
    const data = await listProducts(params)
    if (id !== requestId) return
    products.value = data

    if (!data.items.length && page.value > 1) {
      page.value = 1
    }
  } catch (requestError) {
    if (id !== requestId) return
    error.value = requestError?.message || 'Could not load products.'
  } finally {
    if (id === requestId) loading.value = false
  }
}

async function loadFacets() {
  facetsLoading.value = true
  facetsError.value = ''
  try {
    facets.value = await getProductFacets()
  } catch (requestError) {
    facetsError.value = requestError?.message || 'Facets unavailable.'
  } finally {
    facetsLoading.value = false
  }
}

// Any filter change reloads (resets to page 1); page changes reload too.
watch([() => route.query.q, category, sort], () => {
  if (page.value !== 1) page.value = 1
  else load()
})

watch(page, load, { immediate: true })

onMounted(loadFacets)

function addToCart(product) {
  cart.add(product)
  toast.success(`“${product.title}” added to your cart.`)
}
</script>

<style scoped>
.storefront-view {
  display: flex;
  flex-direction: column;
  gap: 0;
  min-width: 0;
}

/* ---------------- entrance animation ---------------- */

.reveal {
  animation: rise 620ms cubic-bezier(0.22, 1, 0.36, 1) both;
}

.reveal--1 {
  animation-delay: 40ms;
}
.reveal--2 {
  animation-delay: 130ms;
}
.reveal--3 {
  animation-delay: 210ms;
}
.reveal--4 {
  animation-delay: 280ms;
}
.reveal--5 {
  animation-delay: 350ms;
}

@keyframes rise {
  from {
    opacity: 0;
    transform: translateY(22px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

/* ---------------- collection ---------------- */

.collection {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  width: 100%;
  min-width: 0;
  scroll-margin-top: 96px;
}

.collection__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-5);
  flex-wrap: wrap;
}

.collection__titles {
  min-width: 0;
}

.collection__eyebrow {
  margin: 0 0 var(--space-1);
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--color-primary-hover);
}

.collection__title {
  margin: 0;
  font-size: var(--text-2xl);
  line-height: 1.2;
  font-weight: var(--fw-bold);
  letter-spacing: -0.02em;
  color: var(--color-text);
  overflow-wrap: anywhere;
}

.collection__meta {
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.collection__count {
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.collection__tools {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.collection__chips {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-ink);
  border-radius: var(--radius-full);
  background: var(--color-ink);
  color: #fff;
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  cursor: pointer;
  max-width: 260px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background-color var(--transition), color var(--transition);
}

.chip:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-ink);
}

/* ---------------- promo band ---------------- */

.promo {
  margin-top: var(--space-9);
  padding: var(--space-6);
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-5);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
}

.promo__item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  min-width: 0;
}

.promo__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  flex: none;
  border-radius: var(--radius);
  background: var(--color-primary-soft);
  color: var(--color-primary-hover);
}

.promo__title {
  margin: 0 0 2px;
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
}

.promo__text {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.45;
  color: var(--color-text-muted);
}

/* ---------------- responsive ---------------- */

@media (max-width: 1024px) {
  .promo {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .collection__head {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-4);
  }

  .collection__title {
    font-size: var(--text-xl);
  }

  .collection__tools {
    flex-direction: column;
    align-items: stretch;
  }

  .promo {
    margin-top: var(--space-7);
    padding: var(--space-5) var(--space-4);
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
}

@media (prefers-reduced-motion: reduce) {
  .reveal {
    animation: none !important;
    opacity: 1 !important;
    transform: none !important;
  }
}
</style>
