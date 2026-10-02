<template>
  <div class="checkout">
    <OrderSuccessPanel v-if="placedOrder" :order="placedOrder" @continue="continueShopping" />

    <template v-else>
      <header class="checkout__head">
        <div>
          <p class="checkout__eyebrow">Order review</p>
          <h1 class="checkout__title">Checkout</h1>
        </div>
        <p class="checkout__meta">
          <template v-if="cart.isEmpty">Nothing to place yet.</template>
          <template v-else>
            <span class="tabular">{{ cart.itemCount }}</span>
            {{ cart.itemCount === 1 ? 'item' : 'items' }} · prices are re-confirmed by the server
          </template>
        </p>
      </header>

      <div v-if="cart.isEmpty" class="checkout__empty">
        <EmptyState
          icon="bag"
          title="Your cart is empty"
          message="Add a few products from the catalog before heading to checkout."
        >
          <template #actions>
            <BaseButton icon="arrowLeft" @click="goToStore">Back to the store</BaseButton>
          </template>
        </EmptyState>
      </div>

      <div v-else class="checkout__grid">
        <div class="checkout__main">
          <AppCard title="Order information" :subtitle="`${cart.itemCount} items in this order`">
            <div class="checkout__customer">
              <div class="checkout__customer-info">
                <span class="checkout__avatar" aria-hidden="true">{{ customerInitials }}</span>
                <div class="checkout__customer-text">
                  <p class="medium">{{ authStore.userName }}</p>
                  <p class="text-sm muted truncate">{{ authStore.userEmail }}</p>
                </div>
              </div>
            </div>

            <CheckoutLineItems :rows="rows" :loading="pricesLoading" />

            <AppAlert v-if="pricesError" tone="warning" class="checkout__alert">
              {{ pricesError }}
            </AppAlert>
          </AppCard>

          <AppCard title="What happens next">
            <ol class="checkout__steps">
              <li>
                <strong>PostgreSQL</strong> saves the order — it is the source of truth for
                everything on the order details screen;
              </li>
              <li>
                <strong>RabbitMQ</strong> receives a synchronisation message; <strong>Celery</strong>
                consumes it and pushes the order into <strong>Elasticsearch</strong>;
              </li>
              <li>
                The search dashboard then reflects the new order, its status counts and its revenue;
              </li>
            </ol>
          </AppCard>
        </div>

        <aside class="checkout__aside">
          <OrderSummaryCard
            :item-count="cart.itemCount"
            :subtotal="subtotal"
            :placing="placing"
            :disabled="placeDisabled"
            :disabled-reason="placeDisabledReason"
            @place="placeOrder"
          />

          <AppAlert v-if="placeError" tone="danger" class="checkout__alert">
            {{ placeError }}
          </AppAlert>
        </aside>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppCard from '../components/common/AppCard.vue'
import AppAlert from '../components/common/AppAlert.vue'
import BaseButton from '../components/common/BaseButton.vue'
import EmptyState from '../components/common/EmptyState.vue'
import CheckoutLineItems from '../components/checkout/CheckoutLineItems.vue'
import OrderSummaryCard from '../components/checkout/OrderSummaryCard.vue'
import OrderSuccessPanel from '../components/checkout/OrderSuccessPanel.vue'
import { getProduct } from '../api/products'
import { createOrder } from '../api/orders'
import { useCartStore } from '../stores/cart'
import { useAuthStore } from '../stores/auth'
import { useToastStore } from '../stores/toast'
import { formatCurrency } from '../utils/currency'

const router = useRouter()
const cart = useCartStore()
const authStore = useAuthStore()
const toast = useToastStore()

const prices = ref({})
const pricesLoading = ref(false)
const pricesError = ref('')
const placing = ref(false)
const placeError = ref('')
const placedOrder = ref(null)

const cartKey = computed(() => cart.lines.map((line) => line.id).join(','))

const rows = computed(() =>
  cart.lines.map((line) => {
    const info = prices.value[line.id]
    const livePrice = info?.ok ? info.price : null
    const unitPrice = livePrice ?? line.price
    const available = info ? info.ok && info.active !== false : true
    return {
      id: line.id,
      title: info?.ok && info.title ? info.title : line.title,
      sku: (info?.ok && info.sku) || line.sku,
      category: (info?.ok && info.category) || line.category,
      image_url: info?.ok && info.image_url ? info.image_url : line.image_url,
      quantity: line.quantity,
      unitPrice,
      lineTotal: unitPrice * line.quantity,
      unavailable: !available,
    }
  }),
)

const subtotal = computed(() => rows.value.reduce((sum, row) => sum + row.lineTotal, 0))
const hasUnavailable = computed(() => rows.value.some((row) => row.unavailable))

const customerInitials = computed(() => {
  const name = authStore.userName || ''
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('')
})

const placeDisabled = computed(
  () => placing.value || pricesLoading.value || hasUnavailable.value,
)

const placeDisabledReason = computed(() => {
  if (pricesLoading.value) return 'Re-checking current catalog prices…'
  if (hasUnavailable.value) return 'Remove unavailable items to continue.'
  return ''
})

async function loadPrices() {
  const ids = cartKey.value ? cartKey.value.split(',') : []
  if (!ids.length) {
    prices.value = {}
    pricesError.value = ''
    return
  }

  pricesLoading.value = true
  pricesError.value = ''
  try {
    const results = await Promise.allSettled(ids.map((id) => getProduct(id)))
    const map = {}
    const unavailableTitles = []

    results.forEach((result, index) => {
      const id = ids[index]
      if (result.status === 'fulfilled') {
        const product = result.value
        map[id] = {
          ok: true,
          price: product.price,
          title: product.title,
          sku: product.sku,
          category: product.category,
          image_url: product.image_url,
          active: product.active !== false,
        }
        if (product.active === false) unavailableTitles.push(product.title)
      } else {
        map[id] = { ok: false }
        const line = cart.lines.find((entry) => entry.id === id)
        unavailableTitles.push(line?.title || 'An item')
      }
    })

    prices.value = map
    pricesError.value = unavailableTitles.length
      ? `${unavailableTitles.join(', ')} — no longer available in the catalog. Remove them to continue.`
      : ''
  } finally {
    pricesLoading.value = false
  }
}

watch(cartKey, loadPrices, { immediate: true })

async function placeOrder() {
  if (placeDisabled.value) return

  placing.value = true
  placeError.value = ''
  try {
    const order = await createOrder({
      items: cart.lines.map((line) => ({
        product_id: line.id,
        quantity: line.quantity,
      })),
    })
    placedOrder.value = order
    cart.clear()
    toast.success(`Order ${order.order_number} placed — ${formatCurrency(order.total_amount)}.`)
  } catch (requestError) {
    placeError.value = requestError?.message || 'Could not place the order.'
    toast.error(placeError.value)
  } finally {
    placing.value = false
  }
}

function goToStore() {
  router.push({ name: 'storefront' })
}

function continueShopping() {
  router.push({ name: 'storefront' })
}
</script>

<style scoped>
.checkout {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.checkout__head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}

.checkout__eyebrow {
  margin: 0 0 var(--space-1);
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--color-primary-hover);
}

.checkout__title {
  margin: 0;
  font-size: var(--text-3xl);
  font-weight: var(--fw-bold);
  letter-spacing: -0.02em;
  line-height: 1.15;
  color: var(--color-text);
}

.checkout__meta {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.checkout__empty {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.checkout__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(280px, 1fr);
  gap: var(--space-5);
  align-items: start;
}

.checkout__main {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  min-width: 0;
}

.checkout__aside {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  position: sticky;
  top: calc(var(--topbar-h) + var(--space-4));
}

.checkout__customer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-3);
  margin-bottom: var(--space-4);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  flex-wrap: wrap;
}

.checkout__customer-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}

.checkout__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--accent-soft);
  color: var(--accent-text);
  font-weight: var(--fw-semibold);
  flex: none;
}

.checkout__customer-text {
  min-width: 0;
}

.checkout__steps {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  color: var(--text-muted);
  font-size: var(--text-base);
  line-height: var(--lh-base);
}

.checkout__steps strong {
  color: var(--text);
}

.checkout__alert {
  margin-top: var(--space-3);
}

@media (max-width: 960px) {
  .checkout__grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .checkout__aside {
    position: static;
  }
}
</style>