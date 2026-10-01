<template>
  <div class="storefront">
    <header class="topbar">
      <div class="topbar__inner">
        <button
          type="button"
          class="topbar__hamburger only-mobile"
          aria-label="Toggle navigation"
          :aria-expanded="navOpen"
          @click="navOpen = !navOpen"
        >
          <AppIcon :name="navOpen ? 'close' : 'menu'" :size="18" />
        </button>

        <div class="topbar__left">
          <RouterLink to="/" class="brand" aria-label="Meridian home">
            <span class="brand__mark" aria-hidden="true">M</span>
            <span class="brand__name">Meridian</span>
          </RouterLink>

          <nav class="topbar__nav hide-mobile" aria-label="Main">
            <RouterLink to="/" class="topbar__link" exact-active-class="is-active">Store</RouterLink>
            <RouterLink
              v-if="authStore.isAdmin"
              to="/admin/search"
              class="topbar__link"
              active-class="is-active"
            >
              Search dashboard
            </RouterLink>
          </nav>
        </div>

        <div class="topbar__center">
          <div class="topbar__search">
            <BaseInput
              v-model="search"
              icon="search"
              placeholder="Search products…"
              aria-label="Search products"
              @keydown.enter="handleSearchSubmit"
            />
          </div>
        </div>

        <div class="topbar__right">
          <div class="topbar__user" v-if="authStore.isAuthenticated">
            <div class="user-menu">
              <span class="user-menu__name">{{ authStore.userName }}</span>
              <BaseButton
                variant="ghost"
                size="sm"
                @click="logout"
                class="user-menu__logout"
              >
                <AppIcon name="logout" :size="14" />
                <span>Logout</span>
              </BaseButton>
            </div>
          </div>

          <div class="topbar__user" v-else>
            <RouterLink to="/login" class="topbar__link">Sign in</RouterLink>
          </div>

          <button type="button" class="cart-btn" @click="cartOpen = true">
            <AppIcon name="bag" :size="17" />
            <span class="hide-mobile">Cart</span>
            <span v-if="cart.itemCount > 0" class="cart-btn__badge">{{ cart.itemCount }}</span>
            <span class="sr-only">{{ cart.itemCount }} items in cart</span>
          </button>
        </div>
      </div>

      <div v-if="navOpen" class="topbar__panel only-mobile">
        <BaseInput
          v-model="search"
          icon="search"
          placeholder="Search the catalog…"
          aria-label="Search products"
          @keydown.enter="handleSearchSubmit"
        />
        <nav class="topbar__panel-nav" aria-label="Mobile">
          <RouterLink to="/" class="topbar__link" exact-active-class="is-active" @click="navOpen = false">
            Store
          </RouterLink>
          <RouterLink
            v-if="authStore.isAdmin"
            to="/admin/search"
            class="topbar__link"
            active-class="is-active"
            @click="navOpen = false"
          >
            Search dashboard
          </RouterLink>
        </nav>
        <div class="topbar__panel-user" v-if="authStore.isAuthenticated">
          <span class="topbar__panel-user-name">{{ authStore.userName }}</span>
          <BaseButton
            variant="ghost"
            size="sm"
            @click="logout"
            class="topbar__panel-logout"
          >
            <AppIcon name="logout" :size="14" />
            <span>Logout</span>
          </BaseButton>
        </div>
        <div class="topbar__panel-user" v-else>
          <RouterLink to="/login" class="topbar__link" @click="navOpen = false">Sign in</RouterLink>
        </div>
      </div>
    </header>

    <main class="storefront__main">
      <router-view />
    </main>

    <footer class="footer">
      <div class="footer__inner">
        <p class="text-sm muted">
          Meridian demo — catalog in MongoDB, orders in PostgreSQL, search in Elasticsearch;
        </p>
        <p class="text-xs faint">All data shown comes from the live API.</p>
      </div>
    </footer>

    <CartDrawer
      :open="cartOpen"
      @close="cartOpen = false"
      @checkout="goToCheckout"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/common/AppIcon.vue'
import BaseInput from '../components/common/BaseInput.vue'
import BaseButton from '../components/common/BaseButton.vue'
import CartDrawer from '../components/storefront/CartDrawer.vue'
import { useCartStore } from '../stores/cart'
import { useAuthStore } from '../stores/auth'
import { debounce } from '../utils/debounce'

const route = useRoute()
const router = useRouter()
const cart = useCartStore()
const authStore = useAuthStore()

const cartOpen = ref(false)
const navOpen = ref(false)

function goToCheckout() {
  cartOpen.value = false
  router.push({ name: 'checkout' })
}

async function logout() {
  await authStore.logout()
  navOpen.value = false
}

const search = ref(String(route.query.q || ''))

watch(
  () => route.query.q,
  (value) => {
    const next = String(value || '')
    if (next !== search.value) search.value = next
  },
)

const syncSearch = debounce((value) => {
  const query = { ...route.query }
  if (value) query.q = value
  else delete query.q
  router.replace({ query })
}, 350)

watch(search, (value) => syncSearch(value))

function handleSearchSubmit() {
  if (!search.value.trim()) return
  const productsSection = document.querySelector('.storefront-view__products')
  if (productsSection) {
    productsSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

watch(
  () => route.fullPath,
  () => {
    navOpen.value = false
  },
)
</script>

<style scoped>
.storefront {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ---------------- top bar ---------------- */

.topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.topbar__inner {
  max-width: var(--content-max);
  margin: 0 auto;
  min-height: var(--topbar-h);
  padding: var(--space-3) var(--space-6);
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.topbar__hamburger {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
}

.topbar__left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text);
  font-weight: var(--fw-semibold);
  font-size: var(--text-md);
  flex: none;
}

.brand:hover {
  text-decoration: none;
}

.brand__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: var(--on-accent);
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
}

.topbar__nav {
  display: flex;
  gap: var(--space-1);
}

.topbar__link {
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: var(--text-sm);
  font-weight: 500;
  transition: background-color var(--transition), color var(--transition);
}

.topbar__link:hover {
  background: var(--surface-2);
  color: var(--text);
  text-decoration: none;
}

.topbar__link.is-active {
  background: var(--accent-soft);
  color: var(--accent-text);
  font-weight: var(--fw-medium);
}

.topbar__center {
  flex: 1;
  display: flex;
  justify-content: center;
  min-width: 0;
}

.topbar__search {
  width: 100%;
  max-width: 480px;
}

.topbar__right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.topbar__user {
  flex: none;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.user-menu__name {
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--text);
  white-space: nowrap;
}

.user-menu__logout {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
}

.cart-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 40px;
  padding: 0 var(--space-3);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  flex: none;
  transition: background-color var(--transition), border-color var(--transition);
}

.cart-btn:hover {
  background: var(--surface-2);
}

.cart-btn__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  background: var(--accent);
  color: var(--on-accent);
  font-size: 10px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.topbar__panel {
  display: none;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  border-top: 1px solid var(--border);
  background: var(--surface);
}

.topbar__panel-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.topbar__panel-user {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding-top: var(--space-3);
  border-top: 1px solid var(--border);
}

.topbar__panel-user-name {
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--text);
}

.topbar__panel-logout {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  width: fit-content;
}

/* ---------------- main + footer ---------------- */

.storefront__main {
  flex: 1 1 auto;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-8) var(--space-6) var(--space-10);
}

.footer {
  border-top: 1px solid var(--border);
  background: var(--surface);
  margin-top: auto;
}

.footer__inner {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-6) var(--space-6);
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
}

@media (max-width: 900px) {
  .topbar__hamburger {
    display: inline-flex;
  }

  .topbar__nav {
    display: none;
  }

  .topbar__panel {
    display: flex;
  }

  .topbar__center {
    display: none;
  }
}

@media (max-width: 640px) {
  .topbar__inner {
    padding: var(--space-2) var(--space-4);
    gap: var(--space-3);
  }

  .topbar__search,
  .topbar__user {
    display: none;
  }

  .topbar__nav {
    display: none;
  }

  .topbar__right {
    gap: var(--space-2);
  }

  .storefront__main {
    padding: var(--space-6) var(--space-4) var(--space-8);
  }

  .footer__inner {
    padding: var(--space-4);
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>