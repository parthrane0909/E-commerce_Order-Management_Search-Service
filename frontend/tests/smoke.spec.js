import { describe, it, expect, beforeAll } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createRouter, createMemoryHistory } from 'vue-router'
import App from '../src/App.vue'
import StorefrontLayout from '../src/layouts/StorefrontLayout.vue'
import AdminLayout from '../src/layouts/AdminLayout.vue'
import StorefrontView from '../src/views/StorefrontView.vue'
import CheckoutView from '../src/views/CheckoutView.vue'
import AdminSearchView from '../src/views/AdminSearchView.vue'
import OrderDetailsView from '../src/views/OrderDetailsView.vue'
import CatalogAdminView from '../src/views/CatalogAdminView.vue'

/**
 * Full-app render smoke tests: every screen is mounted with the real router
 * and talks to the live API (no mocks). When the backend is reachable the
 * screens must render its data; when it is down they must render a proper
 * error state — never a blank view.
 */

const routes = [
  {
    path: '/',
    component: StorefrontLayout,
    children: [
      { path: '', name: 'storefront', component: StorefrontView },
      { path: 'checkout', name: 'checkout', component: CheckoutView },
    ],
  },
  {
    path: '/admin',
    component: AdminLayout,
    children: [
      { path: 'search', name: 'admin-search', component: AdminSearchView },
      { path: 'orders/:id', name: 'order-details', component: OrderDetailsView },
      { path: 'catalog', name: 'catalog-admin', component: CatalogAdminView },
    ],
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../src/views/LoginView.vue'),
  },
]

let adminToken = null

async function apiIsUp() {
  try {
    const response = await fetch('http://localhost:8000/api/health')
    return response.ok
  } catch {
    return false
  }
}

async function loginAsAdmin() {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'admin@example.com', password: 'admin' }),
  })
  if (!response.ok) return null
  const data = await response.json()
  return data.access_token
}

async function mountAt(path, settleMs = 1500, token = null) {
  const router = createRouter({ history: createMemoryHistory(), routes })
  const pinia = createPinia()
  
  // If we have a token, pre-populate the auth store
  if (token) {
    const { useAuthStore } = await import('../src/stores/auth')
    const authStore = useAuthStore()
    authStore.token = token
    authStore.user = { id: 9, name: 'Admin', email: 'admin@example.com', role: 'ADMIN' }
    localStorage.setItem('meridian.auth.token', token)
    localStorage.setItem('meridian.auth.user', JSON.stringify(authStore.user))
  }
  
  const wrapper = mount(App, { global: { plugins: [router, pinia] } })
  await router.push(path)
  await flushPromises()
  await new Promise((resolve) => setTimeout(resolve, settleMs))
  await flushPromises()
  return wrapper
}

beforeAll(async () => {
  adminToken = await loginAsAdmin()
})

describe('screen render smoke', () => {
  it('storefront renders live catalog products', async () => {
    const up = await apiIsUp()
    const wrapper = await mountAt('/')
    const cards = wrapper.findAll('.product-card').length

    expect(wrapper.find('.brand').exists()).toBe(true)
    if (up) expect(cards).toBeGreaterThan(0)
    else expect(wrapper.text()).toContain('Could not load products')
    wrapper.unmount()
  })

  it('admin search renders KPI cards and Elasticsearch results', async () => {
    const up = await apiIsUp()
    const wrapper = await mountAt('/admin/search', 1500, adminToken)
    const text = wrapper.text()

    expect(text).toContain('Total revenue')
    expect(text).toContain('Filtered orders')
    expect(wrapper.findAll('.kpi').length).toBe(5)

    if (up) {
      expect(wrapper.findAll('.results__row').length).toBeGreaterThan(0)
      expect(text).toContain('orders found')
      // KPI revenue comes from live ES aggregations, not placeholders.
      expect(text).not.toContain('$0.00')
    } else {
      expect(text).toContain('Search is unavailable')
    }
    wrapper.unmount()
  })

  it('checkout renders the empty-cart state without an API call', async () => {
    const wrapper = await mountAt('/checkout', 300)
    expect(wrapper.text()).toContain('Your cart is empty')
    wrapper.unmount()
  })

  it('order details renders a live order from PostgreSQL', async () => {
    const up = await apiIsUp()
    // Order ids are not stable across reseeds — discover one from the API.
    let orderId = 1
    let orderNumber = 'ORD-000001'
    if (up && adminToken) {
      try {
        const response = await fetch('http://localhost:8000/api/search/orders', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${adminToken}`
          },
          body: JSON.stringify({ limit: 1 }),
        })
        const payload = await response.json()
        orderId = payload?.results?.[0]?.order_id ?? orderId
        orderNumber = payload?.results?.[0]?.order_number ?? orderNumber
      } catch {
        // keep the seeded fallback
      }
    }

    const wrapper = await mountAt(`/admin/orders/${orderId}`, 1500, adminToken)
    const text = wrapper.text()

    expect(text).toContain('All orders')
    if (up) {
      expect(text).toContain(orderNumber)
      expect(text).toContain('Source of truth: PostgreSQL')
    } else {
      expect(text.includes('Order not found') || text.includes('Could not load this order')).toBe(
        true,
      )
    }
    wrapper.unmount()
  })

  it('catalog admin renders the live catalog table', async () => {
    const up = await apiIsUp()
    const wrapper = await mountAt('/admin/catalog', 1500, adminToken)
    const text = wrapper.text()

    expect(text).toContain('New product')
    if (up) expect(wrapper.findAll('.catalog__sku').length).toBeGreaterThan(0)
    else expect(text).toContain('Could not load the catalog')
    wrapper.unmount()
  })
})
