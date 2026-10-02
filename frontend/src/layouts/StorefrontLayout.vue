<template>
  <div class="storefront">
    <a href="#products-section" class="skip-link">Skip to products</a>

    <!-- Announcement -->
    <div class="announce">
      <div class="announce__inner">
        <p class="announce__text">
          Free shipping on orders over <strong>₹5,000</strong>
          <span class="announce__divider" aria-hidden="true">•</span>
          <button type="button" class="announce__cta" @click="goToProducts">
            Shop the collection
          </button>
        </p>
      </div>
    </div>

    <!-- Header -->
    <header class="header" :class="{ 'header--searching': searchOpen }">
      <div class="header__inner">
        <button
          type="button"
          class="header__hamburger only-mobile"
          aria-label="Toggle navigation"
          :aria-expanded="navOpen"
          @click="navOpen = !navOpen"
        >
          <AppIcon :name="navOpen ? 'close' : 'menu'" :size="20" />
        </button>

        <div class="header__left">
          <RouterLink to="/" class="brand" aria-label="Meridian home">
            <span class="brand__mark" aria-hidden="true">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 19V6l7 7 7-7v13" />
              </svg>
            </span>
            <span class="brand__name">Meridian</span>
          </RouterLink>

          <nav class="header__nav hide-mobile" aria-label="Main">
            <a href="#/" class="header__link is-active" @click.prevent="goHome">Store</a>
            <a href="#categories-section" class="header__link" @click.prevent="scrollTo('#categories-section')">
              Categories
            </a>
            <a href="#products-section" class="header__link" @click.prevent="goToProducts">
              Deals
            </a>
            <a href="#products-section" class="header__link" @click.prevent="goToProducts">
              New Arrivals
            </a>
            <RouterLink
              v-if="authStore.isAdmin"
              to="/admin/search"
              class="header__link header__link--admin"
            >
              Admin
            </RouterLink>
          </nav>
        </div>

        <!-- One primary search: compact at rest, expands on focus -->
        <form
          class="search"
          :class="{ 'search--open': searchOpen, 'search--has-query': searchInput }"
          role="search"
          @submit.prevent="submitSearch"
        >
          <span class="search__icon" aria-hidden="true">
            <AppIcon name="search" :size="17" />
          </span>
          <input
            ref="searchRef"
            v-model="searchInput"
            class="search__input"
            type="search"
            name="q"
            autocomplete="off"
            aria-label="Search products"
            placeholder="Search products"
            @focus="searchOpen = true"
            @blur="searchOpen = false"
            @keydown.esc="dismissSearch"
          />
          <button
            v-if="searchInput"
            type="button"
            class="search__clear"
            aria-label="Clear search"
            @mousedown.prevent="clearSearch"
          >
            <AppIcon name="close" :size="14" />
          </button>
        </form>

        <div class="header__right">
          <button
            type="button"
            class="search-trigger only-mobile"
            aria-label="Search products"
            @click="openMobileSearch"
          >
            <AppIcon name="search" :size="18" />
          </button>

          <div v-if="authStore.isAuthenticated" class="account hide-sm">
            <span class="account__name">{{ authStore.userName }}</span>
            <button type="button" class="account__logout" @click="logout">
              <AppIcon name="logout" :size="14" />
              <span>Sign out</span>
            </button>
          </div>

          <RouterLink v-else to="/login" class="account__signin hide-sm">
            <AppIcon name="user" :size="16" />
            <span>Sign in</span>
          </RouterLink>

          <button
            type="button"
            class="cart-btn"
            :class="{ 'cart-btn--open': cartOpen }"
            :aria-expanded="cartOpen"
            aria-controls="cart-drawer"
            @click="toggleCart"
          >
            <span class="cart-btn__icon" aria-hidden="true">
              <AppIcon name="bag" :size="18" />
            </span>
            <span class="cart-btn__label">Cart</span>
            <span v-if="cart.itemCount > 0" class="cart-btn__badge">{{ cart.itemCount }}</span>
            <span class="sr-only">{{ cart.itemCount }} items in cart</span>
          </button>
        </div>
      </div>

      <!-- Mobile panel -->
      <transition name="panel">
        <div v-if="navOpen" class="header__panel only-mobile">
          <form class="panel-search" role="search" @submit.prevent="submitSearch">
            <span class="panel-search__icon" aria-hidden="true">
              <AppIcon name="search" :size="16" />
            </span>
            <input
              v-model="searchInput"
              class="panel-search__input"
              type="search"
              autocomplete="off"
              aria-label="Search products"
              placeholder="Search products"
            />
          </form>

          <nav class="header__panel-nav" aria-label="Mobile">
            <a href="#/" class="header__panel-link" @click.prevent="goHome">Store</a>
            <a href="#categories-section" class="header__panel-link" @click.prevent="scrollTo('#categories-section')">
              Categories
            </a>
            <a href="#products-section" class="header__panel-link" @click.prevent="goToProducts">
              Deals
            </a>
            <a href="#products-section" class="header__panel-link" @click.prevent="goToProducts">
              New Arrivals
            </a>
            <RouterLink
              v-if="authStore.isAdmin"
              to="/admin/search"
              class="header__panel-link"
              @click="navOpen = false"
            >
              Admin
            </RouterLink>
          </nav>

          <div class="header__panel-account">
            <template v-if="authStore.isAuthenticated">
              <span class="header__panel-name">{{ authStore.userName }}</span>
              <button type="button" class="account__logout" @click="logout">
                <AppIcon name="logout" :size="14" />
                <span>Sign out</span>
              </button>
            </template>
            <RouterLink v-else to="/login" class="account__signin" @click="navOpen = false">
              <AppIcon name="user" :size="16" />
              <span>Sign in</span>
            </RouterLink>
          </div>
        </div>
      </transition>
    </header>

    <main class="storefront__main">
      <router-view />
    </main>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer__inner">
        <div class="footer__brand">
          <RouterLink to="/" class="brand brand--footer" aria-label="Meridian home">
            <span class="brand__mark" aria-hidden="true">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 19V6l7 7 7-7v13" />
              </svg>
            </span>
            <span class="brand__name">Meridian Store</span>
          </RouterLink>
          <p class="footer__tagline">Everything for the way you work.</p>

          <ul class="footer__contact">
            <li><a href="mailto:hello@meridian.store" class="footer__link">hello@meridian.store</a></li>
            <li><span class="footer__link footer__link--static">Mon–Sat, 9:00–18:00 IST</span></li>
          </ul>
        </div>

        <nav class="footer__nav" aria-label="Footer navigation">
          <div class="footer__group">
            <h4 class="footer__title">Shop</h4>
            <ul>
              <li><button type="button" class="footer__link" @click="goHome">All Products</button></li>
              <li><button type="button" class="footer__link" @click="goCategory('peripherals')">Peripherals</button></li>
              <li><button type="button" class="footer__link" @click="goCategory('audio')">Audio</button></li>
              <li><button type="button" class="footer__link" @click="goCategory('cables')">Cables</button></li>
              <li><button type="button" class="footer__link" @click="goCategory('office')">Office</button></li>
            </ul>
          </div>

          <div class="footer__group">
            <h4 class="footer__title">Support</h4>
            <ul>
              <li><a href="#" class="footer__link" @click.prevent>Contact Us</a></li>
              <li><a href="#" class="footer__link" @click.prevent>Shipping Info</a></li>
              <li><a href="#" class="footer__link" @click.prevent>Returns</a></li>
              <li><a href="#" class="footer__link" @click.prevent>FAQ</a></li>
            </ul>
          </div>

          <div class="footer__group">
            <h4 class="footer__title">Company</h4>
            <ul>
              <li><a href="#" class="footer__link" @click.prevent>About</a></li>
              <li><a href="#" class="footer__link" @click.prevent>Careers</a></li>
              <li><a href="#" class="footer__link" @click.prevent>Press</a></li>
            </ul>
          </div>
        </nav>

        <div class="footer__bottom">
          <ul class="footer__pay" aria-label="Accepted payment methods">
            <li class="footer__pay-chip">UPI</li>
            <li class="footer__pay-chip">Visa</li>
            <li class="footer__pay-chip">Mastercard</li>
            <li class="footer__pay-chip">Rupay</li>
            <li class="footer__pay-chip">COD</li>
          </ul>
          <p class="footer__copy">© {{ year }} Meridian Store</p>
        </div>
      </div>
    </footer>

    <CartDrawer
      id="cart-drawer"
      :open="cartOpen"
      @close="cartOpen = false"
      @checkout="goToCheckout"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppIcon from '../components/common/AppIcon.vue'
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
const searchOpen = ref(false)
const searchRef = ref(null)

const searchInput = ref(String(route.query.q || ''))
const year = new Date().getFullYear()

const hasQuery = computed(() => Boolean(String(route.query.q || '').trim()))

/* ---------------- navigation ---------------- */

function scrollTo(selector) {
  navOpen.value = false
  const el = document.querySelector(selector)
  if (!el) return
  const top = el.getBoundingClientRect().top + window.scrollY - 96
  window.scrollTo({ top, behavior: reducedMotion() ? 'auto' : 'smooth' })
}

function reducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false
}

function goToProducts() {
  navOpen.value = false
  if (route.name !== 'storefront') {
    router.push({ name: 'storefront' }).then(() => scrollTo('#products-section'))
    return
  }
  scrollTo('#products-section')
}

function goHome() {
  navOpen.value = false
  if (route.name !== 'storefront' || Object.keys(route.query).length) {
    router.push({ name: 'storefront' })
    return
  }
  window.scrollTo({ top: 0, behavior: reducedMotion() ? 'auto' : 'smooth' })
}

function goCategory(value) {
  navOpen.value = false
  const query = { category: value }
  if (route.name !== 'storefront') router.push({ name: 'storefront', query })
  else router.replace({ query }).then(() => scrollTo('#products-section'))
}

async function logout() {
  await authStore.logout()
  navOpen.value = false
}

/* ---------------- search ---------------- */

const syncSearch = debounce((value) => {
  const query = { ...route.query }
  const trimmed = String(value || '').trim()
  if (trimmed) query.q = trimmed
  else delete query.q
  delete query.page
  router.replace({ query }).catch(() => {})
}, 260)

watch(searchInput, (value) => syncSearch(value))

function submitSearch() {
  if (!searchInput.value.trim()) return
  searchOpen.value = false
  searchRef.value?.blur()
  goToProducts()
}

function dismissSearch() {
  searchOpen.value = false
  searchRef.value?.blur()
}

function clearSearch() {
  searchInput.value = ''
  searchRef.value?.focus()
}

function openMobileSearch() {
  navOpen.value = true
  nextTick(() => document.querySelector('.panel-search__input')?.focus())
}

/* ---------------- cart ---------------- */

function toggleCart() {
  cartOpen.value = !cartOpen.value
}

function goToCheckout() {
  cartOpen.value = false
  router.push({ name: 'checkout' })
}

/* ---------------- watchers / lifecycle ---------------- */

watch(
  () => route.query.q,
  (value) => {
    const next = String(value || '')
    if (next !== searchInput.value) searchInput.value = next
    if (next.trim() && route.name === 'storefront') {
      nextTick(() => scrollTo('#products-section'))
    }
  },
)

watch(
  () => route.fullPath,
  () => {
    navOpen.value = false
  },
)

function onKeydown(event) {
  if (event.key === 'Escape') {
    navOpen.value = false
    searchOpen.value = false
  }
  if ((event.key === '/' || (event.key === 'k' && (event.metaKey || event.ctrlKey))) && !isTyping(event)) {
    event.preventDefault()
    searchRef.value?.focus()
  }
}

function isTyping(event) {
  const tag = event.target?.tagName
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || event.target?.isContentEditable
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

defineExpose({ hasQuery })
</script>

<style scoped>
.storefront {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}

.skip-link {
  position: fixed;
  top: -100px;
  left: var(--space-4);
  background: var(--color-text);
  color: #fff;
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius);
  z-index: 100;
  font-weight: var(--fw-semibold);
  font-size: var(--text-sm);
  transition: top var(--transition);
}

.skip-link:focus {
  top: var(--space-4);
}

/* ---------------- announcement ---------------- */

.announce {
  background: var(--color-ink);
  color: rgba(255, 255, 255, 0.86);
  font-size: var(--text-sm);
}

.announce__inner {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 9px var(--container-pad);
  display: flex;
  justify-content: center;
}

.announce__text {
  margin: 0;
  text-align: center;
  font-size: var(--text-sm);
  line-height: 1.4;
}

.announce__text strong {
  color: var(--color-primary);
  font-weight: var(--fw-semibold);
}

.announce__divider {
  margin: 0 var(--space-2);
  color: rgba(255, 255, 255, 0.35);
}

.announce__cta {
  border: 0;
  background: none;
  /* keeps the 37px bar visually identical while widening the hit area */
  padding: 6px 4px;
  margin: -6px -4px;
  color: #fff;
  font: inherit;
  font-weight: var(--fw-semibold);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-color: var(--color-primary);
}

.announce__cta:hover {
  color: var(--color-primary);
}

/* ---------------- header ---------------- */

.header {
  position: sticky;
  top: 0;
  z-index: 40;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: saturate(180%) blur(14px);
  -webkit-backdrop-filter: saturate(180%) blur(14px);
  border-bottom: 1px solid var(--color-border);
}

.header__inner {
  max-width: var(--content-max);
  margin: 0 auto;
  min-height: var(--topbar-h);
  padding: var(--space-3) var(--container-pad);
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.header__hamburger {
  display: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
}

.header__hamburger:hover {
  border-color: var(--color-text);
}

.header__left {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  min-width: 0;
}

/* Brand */
.brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text);
  font-weight: var(--fw-bold);
  font-size: var(--text-lg);
  letter-spacing: -0.02em;
  flex: none;
  text-decoration: none;
}

.brand:hover {
  color: var(--color-text);
  text-decoration: none;
}

.brand__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: var(--color-primary);
  color: var(--color-ink);
  box-shadow: var(--shadow-sm);
}

.brand__name {
  white-space: nowrap;
}

/* Nav */
.header__nav {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.header__link {
  position: relative;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius);
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  transition: color var(--transition), background-color var(--transition);
  white-space: nowrap;
}

.header__link:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
  text-decoration: none;
}

.header__link.is-active {
  color: var(--color-text);
  font-weight: var(--fw-semibold);
}

.header__link.is-active::after {
  content: '';
  position: absolute;
  left: var(--space-3);
  right: var(--space-3);
  bottom: 2px;
  height: 2px;
  border-radius: 2px;
  background: var(--color-primary);
}

.header__link--admin {
  color: var(--color-teal);
}

/* ---------------- search ---------------- */

.search {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: 40px;
  width: 210px;
  flex: none;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface-hover);
  cursor: text;
  transition:
    width 280ms cubic-bezier(0.22, 1, 0.36, 1),
    background-color var(--transition),
    border-color var(--transition),
    box-shadow var(--transition);
}

.search:hover {
  border-color: var(--color-border-strong);
}

.search--open,
.search--has-query {
  width: 340px;
  background: var(--color-surface);
  border-color: var(--color-primary);
  box-shadow: var(--focus-ring);
}

.search__icon {
  display: inline-flex;
  color: var(--color-text-muted);
  flex: none;
}

.search--open .search__icon {
  color: var(--color-primary-hover);
}

.search__input {
  flex: 1 1 auto;
  min-width: 0;
  border: 0;
  outline: none;
  background: transparent;
  font-size: var(--text-sm);
  color: var(--color-text);
  -webkit-appearance: none;
  appearance: none;
}

.search__input::placeholder {
  color: var(--color-text-faint);
}

.search__input::-webkit-search-cancel-button {
  display: none;
}

.search__clear {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  flex: none;
  border: 0;
  border-radius: var(--radius-full);
  background: var(--color-border);
  color: var(--color-text-muted);
  cursor: pointer;
}

.search__clear:hover {
  background: var(--color-text);
  color: #fff;
}

/* ---------------- right side ---------------- */

.header__right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-left: auto;
  flex: none;
}

.search-trigger {
  display: none;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
}

.account {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.account__name {
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  color: var(--color-text);
  white-space: nowrap;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.account__signin {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 40px;
  padding: 0 var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  white-space: nowrap;
  transition: border-color var(--transition), background-color var(--transition);
}

.account__signin:hover {
  border-color: var(--color-text);
  text-decoration: none;
}

.account__logout {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  height: 36px;
  padding: 0 var(--space-3);
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  cursor: pointer;
  white-space: nowrap;
}

.account__logout:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

/* ---------------- cart button ---------------- */

.cart-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  height: 44px;
  padding: 0 var(--space-5);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-ink);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  flex: none;
  box-shadow: var(--shadow-sm);
  transition:
    transform 260ms cubic-bezier(0.22, 1, 0.36, 1),
    background-color var(--transition),
    box-shadow var(--transition),
    border-radius var(--transition);
}

.cart-btn:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
  box-shadow: var(--shadow-md);
}

.cart-btn__icon {
  display: flex;
}

/* The button slides toward the left as the drawer expands from the right. */
.cart-btn--open {
  transform: translateX(-10px);
  border-top-right-radius: 6px;
  border-bottom-right-radius: 6px;
  background: var(--color-ink);
  border-color: var(--color-ink);
  color: var(--color-primary);
}

.cart-btn__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 22px;
  height: 22px;
  padding: 0 6px;
  border-radius: var(--radius-full);
  background: var(--color-ink);
  color: var(--color-primary);
  font-size: 11px;
  font-weight: var(--fw-bold);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0;
}

.cart-btn--open .cart-btn__badge {
  background: var(--color-primary);
  color: var(--color-ink);
}

.cart-btn--open .cart-btn__badge,
.cart-btn__badge {
  animation: badge-pop 300ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes badge-pop {
  from {
    transform: scale(0.6);
  }
  to {
    transform: scale(1);
  }
}

/* ---------------- mobile panel ---------------- */

.header__panel {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4) var(--container-pad) var(--space-5);
  border-top: 1px solid var(--color-border);
  background: var(--color-surface);
}

.panel-search {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: 44px;
  padding: 0 var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface-hover);
}

.panel-search__icon {
  display: inline-flex;
  color: var(--color-text-muted);
}

.panel-search__input {
  flex: 1 1 auto;
  min-width: 0;
  border: 0;
  outline: none;
  background: transparent;
  font-size: var(--text-base);
  -webkit-appearance: none;
  appearance: none;
}

.header__panel-nav {
  display: flex;
  flex-direction: column;
}

.header__panel-link {
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text);
  font-size: var(--text-base);
  font-weight: var(--fw-medium);
}

.header__panel-link:last-child {
  border-bottom: 0;
}

.header__panel-link:hover {
  color: var(--color-primary-hover);
  text-decoration: none;
}

.header__panel-account {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding-top: var(--space-2);
}

.header__panel-name {
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
}

.panel-enter-active,
.panel-leave-active {
  transition: opacity 200ms ease, transform 200ms ease;
  overflow: hidden;
}

.panel-enter-from,
.panel-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ---------------- main ---------------- */

.storefront__main {
  flex: 1 1 auto;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-6) var(--container-pad) var(--space-9);
}

/* ---------------- footer ---------------- */

.footer {
  border-top: 1px solid var(--color-border);
  background: var(--color-surface);
  margin-top: auto;
}

.footer__inner {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-9) var(--container-pad) var(--space-6);
  display: grid;
  grid-template-columns: minmax(240px, 1.2fr) 2fr;
  gap: var(--space-8) var(--space-9);
  align-items: start;
}

.footer__brand {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.brand--footer .brand__mark {
  width: 30px;
  height: 30px;
}

.footer__tagline {
  font-size: var(--text-base);
  color: var(--color-text-muted);
  line-height: var(--lh-base);
  margin: 0;
}

.footer__contact {
  list-style: none;
  margin: var(--space-2) 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.footer__nav {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-6);
}

.footer__group ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.footer__title {
  font-size: var(--text-xs);
  font-weight: var(--fw-bold);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-text);
  margin: 0 0 var(--space-1);
}

.footer__link {
  border: 0;
  background: none;
  padding: 0;
  font: inherit;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  text-align: left;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.footer__link:hover {
  color: var(--color-primary-hover);
  text-decoration: none;
}

.footer__link--static {
  cursor: default;
}

.footer__link--static:hover {
  color: var(--color-text-muted);
}

.footer__bottom {
  grid-column: 1 / -1;
  padding-top: var(--space-5);
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.footer__pay {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.footer__pay-chip {
  padding: 5px var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-bg);
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: var(--fw-semibold);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.footer__copy {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--color-text-faint);
}

/* ---------------- responsive ---------------- */

@media (max-width: 1180px) {
  .header__inner {
    gap: var(--space-4);
  }

  .search {
    width: 170px;
  }

  .search--open,
  .search--has-query {
    width: 260px;
  }
}

@media (max-width: 1024px) {
  .header__nav {
    display: none;
  }

  .header__hamburger {
    display: inline-flex;
  }

  .search {
    display: none;
  }

  .search-trigger {
    display: inline-flex;
  }
}

@media (max-width: 768px) {
  .footer__inner {
    grid-template-columns: 1fr;
    gap: var(--space-6);
    padding-top: var(--space-7);
  }

  .footer__nav {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 640px) {
  .header__inner {
    padding: var(--space-2) var(--container-pad);
    gap: var(--space-2);
  }

  .hide-sm {
    display: none !important;
  }

  .account__signin,
  .account {
    display: none;
  }

  .cart-btn {
    height: 40px;
    padding: 0 var(--space-3);
    gap: var(--space-1);
  }

  .cart-btn__label {
    display: none;
  }

  .storefront__main {
    padding-top: var(--space-4);
    padding-bottom: var(--space-7);
  }

  .announce__divider,
  .announce__cta {
    display: none;
  }

  .footer__nav {
    grid-template-columns: 1fr 1fr;
    gap: var(--space-5);
  }

  .footer__bottom {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (prefers-reduced-motion: reduce) {
  .search,
  .cart-btn,
  .panel-enter-active,
  .panel-leave-active {
    transition-duration: 0.01ms !important;
  }
}
</style>
