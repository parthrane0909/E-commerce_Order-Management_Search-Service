<template>
  <div class="search-view">
    <SearchKpis
      :aggregations="data?.aggregations ?? null"
      :total="data?.total ?? 0"
      :loading="loading"
    />

    <SearchFilters
      :query="queryInput"
      :statuses="statuses"
      :date-from="dateFrom"
      :date-to="dateTo"
      :min-price="minPrice"
      :max-price="maxPrice"
      :active-count="activeCount"
      @update:query="queryInput = $event"
      @update:statuses="statuses = $event"
      @update:date-from="dateFrom = $event"
      @update:date-to="dateTo = $event"
      @update:min-price="minPrice = $event"
      @update:max-price="maxPrice = $event"
      @reset="resetFilters"
    />

    <section class="search-view__results">
      <div class="search-view__meta">
        <p class="text-sm muted">
          <template v-if="loading">Searching orders…</template>
          <template v-else-if="error">&nbsp;</template>
          <template v-else>
            <span class="medium tabular">{{ formatNumber(data?.total ?? 0) }}</span>
            {{ (data?.total ?? 0) === 1 ? 'order' : 'orders' }} found
            <span v-if="data?.took_ms != null" class="faint"> · took {{ data.took_ms }} ms</span>
          </template>
        </p>
        <p v-if="!loading && !error && data && data.total > 0" class="text-xs faint">
          Elasticsearch · index refreshes via RabbitMQ → Celery
        </p>
      </div>

      <AppAlert v-if="error" tone="danger" title="Search is unavailable">
        <p>{{ error }}</p>
        <p class="text-sm">
          Elasticsearch may be rebuilding its index — orders remain safe in PostgreSQL and the
          storefront keeps working.
        </p>
        <BaseButton variant="secondary" icon="refresh" class="search-view__retry" @click="refresh">
          Retry
        </BaseButton>
      </AppAlert>

      <AppCard v-else-if="!loading && data && data.total === 0" flush>
        <EmptyState
          icon="search"
          title="No orders match these filters"
          message="Try widening the date range, price range or status selection."
        >
          <template #actions>
            <BaseButton variant="secondary" icon="refresh" @click="resetFilters">
              Reset filters
            </BaseButton>
          </template>
        </EmptyState>
      </AppCard>

      <AppCard v-else flush>
        <div class="only-desktop">
          <ResultsTable :items="data?.results ?? []" :loading="loading" @select="openOrder" />
        </div>
        <div class="only-mobile search-view__cards">
          <ResultsCardList :items="data?.results ?? []" :loading="loading" @select="openOrder" />
        </div>
      </AppCard>

      <AppPagination
        v-if="!error && data && data.pages > 1"
        :page="page"
        :pages="data.pages"
        :total="data.total"
        :loading="loading"
        item-label="orders"
        @update:page="setPage"
      />
    </section>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import SearchKpis from '../components/admin/SearchKpis.vue'
import SearchFilters from '../components/admin/SearchFilters.vue'
import ResultsTable from '../components/admin/ResultsTable.vue'
import ResultsCardList from '../components/admin/ResultsCardList.vue'
import AppCard from '../components/common/AppCard.vue'
import AppAlert from '../components/common/AppAlert.vue'
import AppPagination from '../components/common/AppPagination.vue'
import BaseButton from '../components/common/BaseButton.vue'
import EmptyState from '../components/common/EmptyState.vue'
import { searchOrders } from '../api/search'
import { messageFrom } from '../api/client'
import { formatNumber } from '../utils/currency'
import { debounce } from '../utils/debounce'

const router = useRouter()

const PAGE_SIZE = 20

const queryInput = ref('')
const query = ref('')
const statuses = ref([])
const dateFrom = ref('')
const dateTo = ref('')
const minPrice = ref('')
const maxPrice = ref('')
const page = ref(1)

const data = ref(null)
const loading = ref(false)
const error = ref('')
let requestId = 0

const debouncedQuery = debounce((value) => {
  query.value = value
}, 350)

watch(queryInput, (value) => debouncedQuery(value))

const priceInvalid = computed(
  () =>
    minPrice.value !== '' &&
    maxPrice.value !== '' &&
    Number(minPrice.value) > Number(maxPrice.value),
)

const activeCount = computed(() => {
  let count = 0
  if (queryInput.value.trim()) count += 1
  if (statuses.value.length) count += 1
  if (dateFrom.value) count += 1
  if (dateTo.value) count += 1
  if (minPrice.value !== '') count += 1
  if (maxPrice.value !== '') count += 1
  return count
})

async function refresh() {
  if (priceInvalid.value) return

  const id = (requestId += 1)
  loading.value = true
  error.value = ''
  try {
    const payload = { page: page.value, limit: PAGE_SIZE }
    const term = query.value.trim()
    if (term) payload.query = term
    if (statuses.value.length) payload.status = [...statuses.value]
    if (dateFrom.value) payload.date_from = dateFrom.value
    if (dateTo.value) payload.date_to = dateTo.value
    if (minPrice.value !== '') payload.min_price = Number(minPrice.value)
    if (maxPrice.value !== '') payload.max_price = Number(maxPrice.value)

    const result = await searchOrders(payload)
    if (id !== requestId) return
    data.value = result
  } catch (requestError) {
    if (id !== requestId) return
    error.value = messageFrom(requestError)
  } finally {
    if (id === requestId) loading.value = false
  }
}

function setPage(nextPage) {
  page.value = nextPage
}

function resetFilters() {
  debouncedQuery.cancel()
  queryInput.value = ''
  query.value = ''
  statuses.value = []
  dateFrom.value = ''
  dateTo.value = ''
  minPrice.value = ''
  maxPrice.value = ''
}

function openOrder(orderId) {
  router.push({ name: 'order-details', params: { id: orderId } })
}

// Any filter change restarts from page 1; page changes re-query directly.
watch([query, statuses, dateFrom, dateTo, minPrice, maxPrice], () => {
  if (priceInvalid.value) return
  if (page.value !== 1) page.value = 1
  else refresh()
})

watch(page, refresh, { immediate: true })
</script>

<style scoped>
.search-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.search-view__results {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.search-view__meta {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
  min-height: 20px;
}

.search-view__cards {
  padding: var(--space-3);
}

.search-view__retry {
  margin-top: var(--space-2);
}
</style>
