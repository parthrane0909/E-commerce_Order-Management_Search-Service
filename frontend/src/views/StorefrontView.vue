<template>
  <div class="storefront-view">
    <HeroSection />

    <CategorySection :categories="facets.categories" />

    <div class="storefront-view__products" id="products-section">
      <div class="storefront-view__products-header">
        <div class="storefront-view__meta">
          <p class="text-sm muted">
            <template v-if="loading">Loading products…</template>
            <template v-else-if="error">&nbsp;</template>
            <template v-else>
              <span class="medium tabular">{{ products.total }}</span>
              {{ products.total === 1 ? 'product' : 'products' }}
              <span v-if="hasActiveFilters">matching your filters</span>
            </template>
          </p>
          <p v-if="facetsError" class="text-xs faint">Category counts unavailable.</p>
        </div>

        <ProductFilters
          :search="qInput"
          :category="category"
          :sort="sort"
          :category-facets="facets.categories"
          :tags-loading="facetsLoading"
          :tags-error="facetsError"
          @update:search="onSearchInput"
          @update:category="onCategoryChange"
          @update:sort="onSortChange"
          @reset="resetFilters"
        />
      </div>

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
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ProductFilters from '../components/storefront/ProductFilters.vue'
import ProductGrid from '../components/storefront/ProductGrid.vue'
import AppPagination from '../components/common/AppPagination.vue'
import HeroSection from '../components/storefront/HeroSection.vue'
import CategorySection from '../components/storefront/CategorySection.vue'
import { listProducts, getProductFacets } from '../api/products'
import { useCartStore } from '../stores/cart'
import { useToastStore } from '../stores/toast'
import { debounce } from '../utils/debounce'

const route = useRoute()
const router = useRouter()
const cart = useCartStore()
const toast = useToastStore()

const PAGE_SIZE = 24

function parseIntQuery(value) {
  const parsed = parseInt(String(value || ''), 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 1
}

// Local mirrors of the URL-driven filter state.
const qInput = ref(String(route.query.q || ''))
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

// URL-derived sources: the layout's top-bar search and browser history write
// straight to the query string, so this keeps every screen in sync.
const q = computed(() => String(route.query.q || ''))
const routeCategory = computed(() => String(route.query.category || ''))
const routeSort = computed(() => String(route.query.sort || 'newest'))
const routePage = computed(() => parseIntQuery(route.query.page))

const hasActiveFilters = computed(
  () =>
    Boolean(qInput.value.trim() || category.value) ||
    sort.value !== 'newest',
)

function pushQuery(patch) {
  const query = { ...route.query }
  Object.entries(patch).forEach(([key, value]) => {
    if (value === undefined || value === '' || value === null) delete query[key]
    else query[key] = String(value)
  })
  router.replace({ query })
}

/* ---------------- route -> local sync ---------------- */

watch(q, (value) => {
  if (value !== qInput.value) qInput.value = value
})

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

const debouncedSearch = debounce((value) => {
  pushQuery({ q: value.trim() || undefined })
}, 350)

function onSearchInput(value) {
  qInput.value = value
  debouncedSearch(value)
}

function onCategoryChange(value) {
  category.value = value
  pushQuery({ category: value || undefined, page: undefined })
}

function onSortChange(value) {
  sort.value = value
  pushQuery({ sort: value === 'newest' ? undefined : value, page: undefined })
}

function setPage(nextPage) {
  page.value = nextPage
  pushQuery({ page: nextPage > 1 ? nextPage : undefined })
}

function resetFilters() {
  debouncedSearch.cancel()
  qInput.value = ''
  category.value = ''
  sort.value = 'newest'
  router.replace({ query: {} })
  // When the query was already empty this replace is a duplicate navigation,
  // so no watcher fires — nudge a reload (empty-catalog edge case). Overlapping
  // watcher loads are folded together by the in-flight guard in load().
  if (page.value === 1) load()
}

/* ---------------- fetching ---------------- */

async function load() {
  const params = { page: page.value, limit: PAGE_SIZE, sort: sort.value, visibility: 'active' }
  const term = qInput.value.trim()
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
watch([q, category, sort], () => {
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
  gap: var(--space-4);
}

.storefront-view__products {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.storefront-view__products-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

@media (max-width: 900px) {
  .storefront-view__products-header {
    gap: var(--space-3);
  }
}
</style>