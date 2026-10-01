<template>
  <div class="catalog-view">
    <section class="catalog-toolbar">
      <BaseInput
        class="catalog-toolbar__search"
        v-model="queryInput"
        icon="search"
        placeholder="Search by title, SKU or description…"
        aria-label="Search products"
      />

      <BaseSelect
        class="catalog-toolbar__select"
        v-model="category"
        :options="categoryOptions"
        placeholder="All categories"
        aria-label="Filter by category"
      />

      <BaseSelect
        class="catalog-toolbar__select"
        v-model="visibility"
        :options="VISIBILITY_OPTIONS"
        aria-label="Filter by visibility"
      />

      <BaseButton icon="plus" @click="openCreate">New product</BaseButton>
    </section>

    <div class="catalog-view__meta">
      <p class="text-sm muted">
        <template v-if="loading">Loading products…</template>
        <template v-else-if="error">&nbsp;</template>
        <template v-else>
          <span class="medium tabular">{{ list.total }}</span>
          {{ list.total === 1 ? 'product' : 'products' }}
          <span v-if="activeCount">matching your filters</span>
        </template>
      </p>
      <p v-if="!loading && !error" class="text-xs faint">MongoDB · catalog is the source of truth</p>
    </div>

    <AppAlert v-if="error" tone="danger" title="Could not load the catalog">
      <p>{{ error }}</p>
      <BaseButton variant="secondary" icon="refresh" class="catalog-view__retry" @click="load">
        Retry
      </BaseButton>
    </AppAlert>

    <AppCard v-else-if="!loading && !list.items.length" flush>
      <EmptyState
        icon="package"
        :title="activeCount ? 'No products match these filters' : 'The catalog is empty'"
        :message="
          activeCount
            ? 'Try a different search term, category or visibility setting.'
            : 'Create your first product to get started.'
        "
      >
        <template #actions>
          <BaseButton v-if="activeCount" variant="secondary" icon="refresh" @click="resetFilters">
            Clear filters
          </BaseButton>
          <BaseButton icon="plus" @click="openCreate">New product</BaseButton>
        </template>
      </EmptyState>
    </AppCard>

    <AppCard v-else flush>
      <div class="only-desktop">
        <CatalogTable
          :items="list.items"
          :loading="loading"
          @edit="openEdit"
          @toggle="requestToggle"
        />
      </div>
      <div class="only-mobile catalog-view__cards">
        <CatalogCardList :items="list.items" @edit="openEdit" @toggle="requestToggle" />
      </div>
    </AppCard>

    <AppPagination
      v-if="!error && list.pages > 1"
      :page="page"
      :pages="list.pages"
      :total="list.total"
      :loading="loading"
      item-label="products"
      @update:page="setPage"
    />

    <ProductFormModal
      :open="formOpen"
      :product="editing"
      @close="formOpen = false"
      @saved="onSaved"
    />

    <ConfirmDialog
      :open="confirmOpen"
      title="Deactivate product?"
      :message="
        confirmTarget
          ? `“${confirmTarget.title}” will be deactivated and hidden from the storefront. Product is deactivated; historical orders keep their snapshot.`
          : ''
      "
      confirm-label="Deactivate"
      tone="danger"
      :loading="confirmBusy"
      @confirm="confirmDeactivate"
      @cancel="confirmOpen = false"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import BaseInput from '../components/common/BaseInput.vue'
import BaseSelect from '../components/common/BaseSelect.vue'
import BaseButton from '../components/common/BaseButton.vue'
import AppCard from '../components/common/AppCard.vue'
import AppAlert from '../components/common/AppAlert.vue'
import AppPagination from '../components/common/AppPagination.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ConfirmDialog from '../components/common/ConfirmDialog.vue'
import CatalogTable from '../components/admin/CatalogTable.vue'
import CatalogCardList from '../components/admin/CatalogCardList.vue'
import ProductFormModal from '../components/admin/ProductFormModal.vue'
import { deleteProduct, getProductFacets, listProducts, updateProduct } from '../api/products'
import { useToastStore } from '../stores/toast'
import { debounce } from '../utils/debounce'

const PAGE_SIZE = 12

const VISIBILITY_OPTIONS = [
  { value: 'all', label: 'All products' },
  { value: 'active', label: 'Active only' },
  { value: 'inactive', label: 'Inactive only' },
]

const toast = useToastStore()

const queryInput = ref('')
const query = ref('')
const category = ref('')
const visibility = ref('all')
const page = ref(1)

const list = ref({ items: [], total: 0, pages: 0, page: 1, limit: PAGE_SIZE })
const facets = ref([])
const loading = ref(false)
const error = ref('')
let requestId = 0

const formOpen = ref(false)
const editing = ref(null)

const confirmOpen = ref(false)
const confirmTarget = ref(null)
const confirmBusy = ref(false)

const debouncedQuery = debounce((value) => {
  query.value = value
}, 350)

watch(queryInput, (value) => debouncedQuery(value))

const activeCount = computed(() => {
  let count = 0
  if (query.value.trim()) count += 1
  if (category.value) count += 1
  if (visibility.value !== 'all') count += 1
  return count
})

const categoryOptions = computed(() =>
  facets.value.map((facet) => ({
    value: facet.value,
    label: `${facet.value} (${facet.count})`,
  })),
)

async function load() {
  const id = (requestId += 1)
  loading.value = true
  error.value = ''
  try {
    const params = {
      page: page.value,
      limit: PAGE_SIZE,
      visibility: visibility.value,
      sort: 'newest',
    }
    const term = query.value.trim()
    if (term) params.q = term
    if (category.value) params.category = category.value

    const data = await listProducts(params)
    if (id !== requestId) return

    if (!data.items.length && page.value > 1) {
      page.value = 1
      return
    }
    list.value = data
  } catch (requestError) {
    if (id !== requestId) return
    error.value = requestError?.message || 'Could not load products.'
  } finally {
    if (id === requestId) loading.value = false
  }
}

async function loadFacets() {
  try {
    const data = await getProductFacets()
    facets.value = data.categories || []
  } catch {
    facets.value = []
  }
}

function setPage(nextPage) {
  page.value = nextPage
}

function resetFilters() {
  debouncedQuery.cancel()
  queryInput.value = ''
  query.value = ''
  category.value = ''
  visibility.value = 'all'
}

/* ---------------- create / edit ---------------- */

function openCreate() {
  editing.value = null
  formOpen.value = true
}

function openEdit(product) {
  editing.value = product
  formOpen.value = true
}

function onSaved(product, mode) {
  if (mode === 'created') toast.success(`“${product.title}” created.`)
  else toast.success(`“${product.title}” updated.`)
  load()
}

/* ---------------- activate / deactivate ---------------- */

function requestToggle(product) {
  if (product.active) {
    confirmTarget.value = product
    confirmOpen.value = true
    return
  }
  activate(product)
}

async function activate(product) {
  try {
    await updateProduct(product.id, { active: true })
    toast.success(`“${product.title}” is active again.`)
    load()
  } catch (requestError) {
    toast.error(requestError?.message || 'Could not activate the product.')
  }
}

async function confirmDeactivate() {
  if (!confirmTarget.value || confirmBusy.value) return
  confirmBusy.value = true
  try {
    await deleteProduct(confirmTarget.value.id)
    toast.success(`“${confirmTarget.value.title}” deactivated — historical orders keep their snapshot.`)
    confirmOpen.value = false
    confirmTarget.value = null
    load()
  } catch (requestError) {
    toast.error(requestError?.message || 'Could not deactivate the product.')
  } finally {
    confirmBusy.value = false
  }
}

// Any filter change restarts from page 1; page changes re-query directly.
watch([query, category, visibility], () => {
  if (page.value !== 1) page.value = 1
  else load()
})

watch(page, load, { immediate: true })

onMounted(loadFacets)
</script>

<style scoped>
.catalog-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.catalog-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
  padding: var(--space-4);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-1);
}

.catalog-toolbar__search {
  flex: 1 1 300px;
}

.catalog-toolbar__select {
  flex: 0 1 190px;
}

.catalog-view__meta {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
  min-height: 20px;
}

.catalog-view__retry {
  margin-top: var(--space-2);
}

.catalog-view__cards {
  padding: var(--space-3);
}

@media (max-width: 640px) {
  .catalog-toolbar__select {
    flex: 1 1 150px;
  }
}
</style>
