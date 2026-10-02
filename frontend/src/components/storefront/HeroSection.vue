<template>
  <section class="hero" aria-labelledby="hero-heading">
    <div class="hero__bg" aria-hidden="true">
      <span class="hero__blob hero__blob--one" />
      <span class="hero__blob hero__blob--two" />
    </div>

    <div class="hero__inner">
      <div class="hero__copy">
        <p class="hero__eyebrow">
          <span class="hero__eyebrow-dot" aria-hidden="true" />
          Meridian Store
        </p>

        <h1 id="hero-heading" class="hero__title">
          Everything you need for the way you <span class="hero__accent">work.</span>
        </h1>

        <p class="hero__subtitle">
          Explore curated peripherals, audio, cables and workspace essentials — chosen for people
          who spend their days at a desk.
        </p>

        <div class="hero__actions">
          <BaseButton size="lg" variant="primary" icon="arrowRight" @click="go('#products-section')">
            Shop Collection
          </BaseButton>
          <BaseButton size="lg" variant="secondary" icon="grid" @click="go('#categories-section')">
            Explore Categories
          </BaseButton>
        </div>

        <ul class="hero__trust">
          <li class="hero__trust-item">
            <span class="hero__trust-icon" aria-hidden="true"><AppIcon name="truck" :size="17" /></span>
            <span>Free shipping over ₹5,000</span>
          </li>
          <li class="hero__trust-item">
            <span class="hero__trust-icon" aria-hidden="true"><AppIcon name="undo" :size="17" /></span>
            <span>30-day returns</span>
          </li>
          <li class="hero__trust-item">
            <span class="hero__trust-icon" aria-hidden="true"><AppIcon name="shield" :size="17" /></span>
            <span>Secure checkout</span>
          </li>
        </ul>
      </div>

      <!-- Visual: live products from the catalog -->
      <div class="hero__visual">
        <div v-if="loading" class="hero__skeleton" aria-hidden="true">
          <div class="hero__skel hero__skel--main" />
          <div class="hero__skel hero__skel--small" />
          <div class="hero__skel hero__skel--small" />
        </div>

        <div v-else-if="featured" class="hero__showcase">
          <article class="hero__featured">
            <div class="hero__featured-media">
              <ProductThumb :product="featured" size="md" />
            </div>
            <div class="hero__featured-body">
              <span class="hero__kicker">Featured</span>
              <p class="hero__featured-cat">{{ formatCategory(featured.category) }}</p>
              <h2 class="hero__featured-title">{{ featured.title }}</h2>
              <div class="hero__featured-foot">
                <span class="hero__featured-price tabular">{{ formatCurrency(featured.price) }}</span>
                <button type="button" class="hero__featured-link" @click="addFeatured">
                  Add to cart
                  <AppIcon name="arrowRight" :size="15" />
                </button>
              </div>
            </div>
          </article>

          <div class="hero__previews">
            <button
              v-for="product in previews"
              :key="product.id"
              type="button"
              class="hero__preview"
              @click="addPreview(product)"
            >
              <span class="hero__preview-media">
                <ProductThumb :product="product" size="md" />
              </span>
              <span class="hero__preview-body">
                <span class="hero__preview-title">{{ product.title }}</span>
                <span class="hero__preview-price tabular">{{ formatCurrency(product.price) }}</span>
              </span>
            </button>
          </div>
        </div>

        <!-- Never an empty rectangle: graceful fallback -->
        <div v-else class="hero__fallback">
          <span class="hero__fallback-icon" aria-hidden="true">
            <AppIcon name="box" :size="30" />
          </span>
          <p class="hero__fallback-title">The catalog is loading</p>
          <p class="hero__fallback-text">Browse every product once it arrives.</p>
          <BaseButton variant="primary" size="md" @click="go('#products-section')">
            Browse products
          </BaseButton>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import BaseButton from '../common/BaseButton.vue'
import AppIcon from '../common/AppIcon.vue'
import ProductThumb from '../common/ProductThumb.vue'
import { formatCurrency } from '../../utils/currency'
import { listProducts } from '../../api/products'
import { useCartStore } from '../../stores/cart'
import { useToastStore } from '../../stores/toast'

const cart = useCartStore()
const toast = useToastStore()

const loading = ref(true)
const items = ref([])

const featured = computed(() => items.value[0] || null)
const previews = computed(() => items.value.slice(1, 3))

function formatCategory(value) {
  const raw = String(value || '')
  return raw.charAt(0).toUpperCase() + raw.slice(1)
}

function reducedMotion() {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false
}

function go(selector) {
  const el = document.querySelector(selector)
  if (!el) return
  const top = el.getBoundingClientRect().top + window.scrollY - 96
  window.scrollTo({ top, behavior: reducedMotion() ? 'auto' : 'smooth' })
}

function addFeatured() {
  if (featured.value) add(featured.value)
}

function addPreview(product) {
  add(product)
}

function add(product) {
  cart.add(product)
  toast.success(`“${product.title}” added to your cart.`)
}

/** Deterministic pick from the live catalog: newest active products. */
async function loadHeroProducts() {
  loading.value = true
  try {
    const data = await listProducts({ limit: 5, sort: 'newest', visibility: 'active' })
    items.value = data.items || []
  } catch {
    items.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadHeroProducts)
</script>

<style scoped>
.hero {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius-xl);
  background: var(--color-ink);
  color: #fff;
  margin-bottom: var(--space-8);
}

.hero__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero__blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(10px);
}

.hero__blob--one {
  width: 460px;
  height: 460px;
  top: -180px;
  right: -80px;
  background: radial-gradient(circle at 30% 30%, rgba(255, 172, 28, 0.5), transparent 70%);
}

.hero__blob--two {
  width: 380px;
  height: 380px;
  bottom: -200px;
  left: -120px;
  background: radial-gradient(circle at 60% 40%, rgba(255, 172, 28, 0.18), transparent 70%);
}

.hero__inner {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  gap: var(--space-8);
  align-items: center;
  padding: var(--space-9) var(--space-8);
}

.hero__copy {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  max-width: 600px;
  animation: hero-in 600ms cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes hero-in {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

.hero__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  width: fit-content;
  margin: 0;
  padding: 6px var(--space-3);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.86);
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero__eyebrow-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(255, 172, 28, 0.22);
}

.hero__title {
  margin: 0;
  font-size: clamp(34px, 4.4vw, 60px);
  line-height: 1.04;
  font-weight: var(--fw-bold);
  letter-spacing: -0.03em;
  color: #fff;
}

.hero__accent {
  color: var(--color-primary);
}

.hero__subtitle {
  margin: 0;
  font-size: clamp(16px, 1.3vw, 19px);
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.7);
  max-width: 480px;
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-1);
}

.hero__actions :deep(.btn--secondary) {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.24);
  color: #fff;
}

.hero__actions :deep(.btn--secondary:hover) {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.45);
}

.hero__trust {
  list-style: none;
  margin: var(--space-3) 0 0;
  padding: var(--space-5) 0 0;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3) var(--space-6);
}

.hero__trust-item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: rgba(255, 255, 255, 0.72);
}

.hero__trust-icon {
  display: inline-flex;
  color: var(--color-primary);
}

/* ---------------- visual ---------------- */

.hero__visual {
  min-height: 420px;
  display: flex;
  align-items: stretch;
}

.hero__showcase {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: var(--space-4);
  width: 100%;
  min-height: 420px;
  animation: hero-in 700ms 80ms cubic-bezier(0.22, 1, 0.36, 1) both;
}

.hero__featured {
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-lg);
}

.hero__featured-media {
  position: relative;
  width: 100%;
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
  background: var(--color-bg);
}

/* Let the media absorb any leftover height so the body never floats in space. */
.hero__featured-media :deep(.thumb) {
  width: 100%;
  height: 100%;
  aspect-ratio: auto;
}

.hero__featured-body {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-4);
  margin-top: -34px;
  background: var(--color-surface);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.hero__kicker {
  position: absolute;
  top: -66px;
  left: var(--space-4);
  padding: 5px var(--space-3);
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-ink);
  font-size: 10px;
  font-weight: var(--fw-bold);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.hero__featured-cat {
  margin: 0;
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--color-text-faint);
}

.hero__featured-title {
  margin: 0;
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
  line-height: 1.35;
  color: var(--color-text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hero__featured-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.hero__featured-price {
  font-size: var(--text-xl);
  font-weight: var(--fw-bold);
  color: var(--color-text);
}

.hero__featured-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: none;
  /* generous hit area without moving the row */
  padding: var(--space-2) 0;
  margin: calc(var(--space-2) * -1) 0;
  color: var(--color-primary-hover);
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  cursor: pointer;
}

.hero__featured-link:hover {
  color: var(--color-ink);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.hero__previews {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.hero__preview {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  text-align: left;
  padding: 0;
  border: 0;
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  overflow: hidden;
  cursor: pointer;
  box-shadow: var(--shadow-md);
  transition: transform var(--transition), box-shadow var(--transition);
}

.hero__preview:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

.hero__preview-media {
  display: block;
  width: 100%;
  max-height: 132px;
  overflow: hidden;
  background: var(--color-bg);
}

.hero__preview-media :deep(.thumb) {
  aspect-ratio: 16 / 9;
}

.hero__preview-body {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-2);
  padding: var(--space-3);
}

.hero__preview-title {
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  color: var(--color-text);
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hero__preview-price {
  font-size: var(--text-sm);
  font-weight: var(--fw-bold);
  color: var(--color-primary-hover);
  white-space: nowrap;
}

/* ---------------- skeleton ---------------- */

.hero__skeleton {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: var(--space-4);
  width: 100%;
}

.hero__skel {
  border-radius: var(--radius-lg);
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.06) 25%,
    rgba(255, 255, 255, 0.14) 50%,
    rgba(255, 255, 255, 0.06) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

.hero__skel--main {
  grid-row: span 2;
  min-height: 340px;
}

.hero__skel--small {
  min-height: 160px;
}

@keyframes shimmer {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}

/* ---------------- fallback ---------------- */

.hero__fallback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-8) var(--space-5);
  border: 1px dashed rgba(255, 255, 255, 0.24);
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.04);
  text-align: center;
}

.hero__fallback-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: var(--radius-full);
  background: rgba(255, 172, 28, 0.16);
  color: var(--color-primary);
}

.hero__fallback-title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--fw-semibold);
  color: #fff;
}

.hero__fallback-text {
  margin: 0;
  font-size: var(--text-sm);
  color: rgba(255, 255, 255, 0.66);
}

/* ---------------- responsive ---------------- */

@media (max-width: 1100px) {
  .hero__inner {
    grid-template-columns: 1fr;
    gap: var(--space-7);
    padding: var(--space-8) var(--space-6);
  }

  .hero__copy {
    max-width: none;
  }

  .hero__visual {
    min-height: 0;
  }

  .hero__showcase,
  .hero__skeleton {
    grid-template-columns: 1fr 1fr;
  }

  .hero__skel--main {
    grid-row: auto;
    min-height: 200px;
  }
}

@media (max-width: 768px) {
  .hero {
    border-radius: var(--radius-lg);
    margin-bottom: var(--space-6);
  }

  .hero__inner {
    padding: var(--space-6) var(--space-5);
    gap: var(--space-6);
  }

  .hero__actions {
    flex-direction: column;
    align-items: stretch;
  }

  .hero__actions :deep(.btn) {
    width: 100%;
  }

  .hero__trust {
    flex-direction: column;
    gap: var(--space-3);
  }

  .hero__showcase,
  .hero__skeleton {
    grid-template-columns: 1fr;
  }

  .hero__previews {
    flex-direction: row;
  }

  .hero__preview {
    min-width: 0;
  }
}

@media (max-width: 480px) {
  .hero__inner {
    padding: var(--space-5) var(--space-4);
  }

  .hero__previews {
    gap: var(--space-3);
  }

  .hero__preview-body {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero__copy,
  .hero__showcase,
  .hero__skel,
  .hero__preview {
    animation: none !important;
    transition: none !important;
  }
}
</style>
