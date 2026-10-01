import { createRouter, createWebHistory } from 'vue-router'
import StorefrontLayout from '../layouts/StorefrontLayout.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { title: 'Sign in', guest: true },
  },
  {
    path: '/',
    component: StorefrontLayout,
    children: [
      {
        path: '',
        name: 'storefront',
        component: () => import('../views/StorefrontView.vue'),
        meta: { title: 'Storefront' },
      },
      {
        path: 'checkout',
        name: 'checkout',
        component: () => import('../views/CheckoutView.vue'),
        meta: { title: 'Checkout', requiresAuth: true },
      },
    ],
  },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: { name: 'admin-search' } },
      {
        path: 'search',
        name: 'admin-search',
        component: () => import('../views/AdminSearchView.vue'),
        meta: { title: 'Search dashboard' },
      },
      {
        path: 'orders/:id',
        name: 'order-details',
        component: () => import('../views/OrderDetailsView.vue'),
        meta: { title: 'Order details' },
      },
      {
        path: 'catalog',
        name: 'catalog-admin',
        component: () => import('../views/CatalogAdminView.vue'),
        meta: { title: 'Catalog admin' },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: { name: 'storefront' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Initialize auth store on first navigation
  if (!authStore.loading && authStore.token && !authStore.user) {
    await authStore.fetchMe()
  }

  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some((record) => record.meta.requiresAdmin)
  const isGuest = to.matched.some((record) => record.meta.guest)

  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login with current path as redirect
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }

  if (requiresAdmin && !authStore.isAdmin) {
    // Non-admin users cannot access admin routes
    return next({ name: 'storefront' })
  }

  if (isGuest && authStore.isAuthenticated) {
    // Authenticated users shouldn't see login page
    return next({ name: 'storefront' })
  }

  next()
})

router.afterEach((to) => {
  const title = to.meta?.title
  document.title = title ? `${title} · Meridian` : 'Meridian — Order Management Demo'
})

export default router