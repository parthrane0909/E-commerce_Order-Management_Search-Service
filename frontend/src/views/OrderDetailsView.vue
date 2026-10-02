<template>
  <div class="order-view">
    <RouterLink :to="{ name: 'admin-search' }" class="order-view__back">
      <AppIcon name="arrowLeft" :size="15" />
      All orders
    </RouterLink>

    <!-- ---------------- loading ---------------- -->
    <template v-if="loading">
      <div class="order-view__head order-view__head--skeleton">
        <LoadingSkeleton variant="block" width="220px" height="28" />
        <LoadingSkeleton variant="block" width="340px" height="34" />
      </div>
      <div class="order-view__grid">
        <LoadingSkeleton variant="block" height="132" />
        <LoadingSkeleton variant="block" height="132" />
        <LoadingSkeleton variant="block" height="200" />
      </div>
    </template>

    <!-- ---------------- not found ---------------- -->
    <div v-else-if="notFound" class="order-view__panel">
      <EmptyState
        icon="search"
        title="Order not found"
        message="This order id does not exist in PostgreSQL — it may have been removed or the link is out of date."
      >
        <template #actions>
          <BaseButton icon="arrowLeft" @click="goBack">Back to search dashboard</BaseButton>
        </template>
      </EmptyState>
    </div>

    <!-- ---------------- error ---------------- -->
    <div v-else-if="error" class="order-view__panel">
      <AppAlert tone="danger" title="Could not load this order">
        {{ error }}
      </AppAlert>
      <BaseButton variant="secondary" icon="refresh" @click="load">Retry</BaseButton>
    </div>

    <!-- ---------------- loaded ---------------- -->
    <template v-else-if="order">
      <header class="order-view__head">
        <div class="order-view__title">
          <div class="row-sm wrap">
            <h2 class="order-view__number tabular">{{ order.order_number }}</h2>
            <AppBadge tone="info" size="sm">Source of truth: PostgreSQL</AppBadge>
          </div>
          <p class="text-sm muted">
            {{ formatDateTime(order.order_date) }} (UTC) ·
            <span class="tabular">order #{{ order.id }}</span>
          </p>
        </div>

        <div class="order-view__controls">
          <SearchSyncIndicator :indexed-at="order.search_indexed_at" />
          <OrderStatusControl
            :status="order.status"
            :pending="pendingStatus"
            :updating="updatingStatus"
            @change="onStatusChange"
          />
        </div>
      </header>

      <div class="order-view__grid">
        <AppCard title="Customer">
          <dl class="order-view__facts">
            <div>
              <dt>Name</dt>
              <dd class="medium">{{ order.customer?.name }}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd class="truncate">{{ order.customer?.email }}</dd>
            </div>
            <div>
              <dt>Customer id</dt>
              <dd class="tabular">{{ order.customer?.id ?? order.user_id }}</dd>
            </div>
          </dl>
        </AppCard>

        <AppCard title="Totals">
          <dl class="order-view__facts">
            <div>
              <dt>Line items</dt>
              <dd class="tabular">{{ order.items?.length || 0 }}</dd>
            </div>
            <div>
              <dt>Units</dt>
              <dd class="tabular">{{ totalUnits }}</dd>
            </div>
            <div>
              <dt>Total</dt>
              <dd class="order-view__total tabular">{{ formatCurrency(order.total_amount) }}</dd>
            </div>
          </dl>
        </AppCard>

        <AppCard
          title="Line items"
          subtitle="Snapshot values recorded when the order was placed — later catalog edits never change them."
          class="order-view__items"
          flush
        >
          <div class="table-scroll">
            <table class="data-table order-view__table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Product</th>
                  <th class="order-view__right">Qty</th>
                  <th class="order-view__right">Unit price</th>
                  <th class="order-view__right">Line total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in order.items" :key="item.id">
                  <td class="muted">{{ index + 1 }}</td>
                  <td>
                    <p class="medium">{{ item.title }}</p>
                    <p class="text-xs muted truncate">{{ item.product_id }}</p>
                  </td>
                  <td class="order-view__right tabular">{{ item.quantity }}</td>
                  <td class="order-view__right tabular">{{ formatCurrency(item.unit_price) }}</td>
                  <td class="order-view__right tabular semibold">
                    {{ formatCurrency(item.line_total) }}
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr>
                  <td colspan="4" class="order-view__subtotal-label">Total</td>
                  <td class="order-view__right tabular semibold">
                    {{ formatCurrency(order.total_amount) }}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </AppCard>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/common/AppIcon.vue'
import AppBadge from '../components/common/AppBadge.vue'
import AppCard from '../components/common/AppCard.vue'
import AppAlert from '../components/common/AppAlert.vue'
import BaseButton from '../components/common/BaseButton.vue'
import EmptyState from '../components/common/EmptyState.vue'
import LoadingSkeleton from '../components/common/LoadingSkeleton.vue'
import OrderStatusControl from '../components/admin/OrderStatusControl.vue'
import SearchSyncIndicator from '../components/admin/SearchSyncIndicator.vue'
import { getOrder, updateOrderStatus } from '../api/orders'
import { useToastStore } from '../stores/toast'
import { formatCurrency } from '../utils/currency'
import { formatDateTime } from '../utils/dates'
import { statusLabel } from '../utils/status'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const order = ref(null)
const loading = ref(true)
const error = ref('')
const notFound = ref(false)
const pendingStatus = ref('')
const updatingStatus = ref(false)

const totalUnits = computed(() =>
  (order.value?.items || []).reduce((sum, item) => sum + item.quantity, 0),
)

async function load() {
  const id = route.params.id
  loading.value = true
  error.value = ''
  notFound.value = false
  try {
    order.value = await getOrder(id)
  } catch (requestError) {
    if (requestError?.status === 404) {
      notFound.value = true
      order.value = null
    } else {
      error.value = requestError?.message || 'Could not load this order.'
    }
  } finally {
    loading.value = false
  }
}

async function onStatusChange(value) {
  if (!value || !order.value || updatingStatus.value) return
  if (value === order.value.status) return

  updatingStatus.value = true
  pendingStatus.value = value
  try {
    const updated = await updateOrderStatus(order.value.id, value)
    order.value = updated
    toast.success(`${order.value.order_number} is now ${statusLabel(value).toLowerCase()}.`)
  } catch (requestError) {
    toast.error(requestError?.message || 'Could not update the status.')
  } finally {
    updatingStatus.value = false
    pendingStatus.value = ''
  }
}

function goBack() {
  router.push({ name: 'admin-search' })
}

watch(
  () => route.params.id,
  () => {
    order.value = null
    load()
  },
  { immediate: true },
)
</script>

<style scoped>
.order-view {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.order-view__back {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  align-self: flex-start;
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.order-view__back:hover {
  color: var(--accent-text);
}

.order-view__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-1);
  flex-wrap: wrap;
}

.order-view__head--skeleton {
  gap: var(--space-3);
}

.order-view__number {
  font-size: var(--text-xl);
  font-variant-numeric: tabular-nums;
}

.order-view__title {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 0;
}

.order-view__controls {
  display: flex;
  align-items: flex-end;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.order-view__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
  align-items: start;
}

.order-view__items {
  grid-column: 1 / -1;
}

.order-view__facts {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.order-view__facts dt {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.order-view__facts dd {
  margin: 0;
  font-size: var(--text-base);
}

.order-view__total {
  font-size: var(--text-lg);
  font-weight: var(--fw-semibold);
}

.order-view__table {
  min-width: 620px;
}

.order-view__table tfoot td {
  border-top: 1px solid var(--border);
  border-bottom: 0;
  background: var(--surface-2);
}

.order-view__right {
  text-align: right;
}

.order-view__subtotal-label {
  text-align: right;
  font-weight: var(--fw-medium);
  color: var(--text-muted);
}

.order-view__panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-5);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.order-view__panel .alert {
  width: 100%;
}

@media (max-width: 800px) {
  .order-view__grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .order-view__head {
    flex-direction: column;
  }
}
</style>
