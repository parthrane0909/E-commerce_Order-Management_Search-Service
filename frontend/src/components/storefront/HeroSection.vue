<template>
  <section class="hero" aria-labelledby="hero-heading">
    <div class="hero__content">
      <h1 id="hero-heading" class="hero__title">
        Everything you need for your workspace
      </h1>
      <p class="hero__subtitle">
        From ergonomic peripherals to desk essentials — curated tech and accessories
        that help you work better, wherever you are.
      </p>
      <RouterLink to="/" class="hero__cta">
        <BaseButton size="lg" icon="arrowRight">
          Shop Now
        </BaseButton>
      </RouterLink>
    </div>
    <div class="hero__visual" aria-hidden="true">
      <div class="hero__product-showcase">
        <div class="showcase-card" v-for="(product, index) in featuredProducts" :key="product.id">
          <ProductThumb :product="product" size="lg" />
          <div class="showcase-card__info">
            <span class="showcase-card__category">{{ product.category }}</span>
            <h3 class="showcase-card__title">{{ product.title }}</h3>
            <span class="showcase-card__price">{{ formatCurrency(product.price) }}</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BaseButton from '../common/BaseButton.vue'
import ProductThumb from '../common/ProductThumb.vue'
import { formatCurrency } from '../../utils/currency'
import { listProducts } from '../../api/products'

const router = useRouter()

const featuredProducts = ref([])

async function loadFeaturedProducts() {
  try {
    const data = await listProducts({ limit: 4, sort: 'newest', visibility: 'active' })
    featuredProducts.value = data.items
  } catch (e) {
    featuredProducts.value = []
  }
}

loadFeaturedProducts()
</script>

<style scoped>
.hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-10);
  align-items: center;
  padding: var(--space-12) var(--space-8);
  max-width: var(--content-max);
  margin: 0 auto;
  background: linear-gradient(135deg, var(--surface) 0%, var(--surface-2) 100%);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  margin-bottom: var(--space-10);
}

.hero__content {
  display: flex;
  flex-direction: column;
  gap: var(--space-7);
  max-width: 520px;
}

.hero__title {
  font-size: var(--text-2xl);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: var(--text);
}

.hero__subtitle {
  font-size: var(--text-lg);
  line-height: 1.6;
  color: var(--text-muted);
  max-width: 440px;
}

.hero__cta {
  margin-top: var(--space-4);
  width: fit-content;
}

.hero__visual {
  display: flex;
  justify-content: center;
}

.hero__product-showcase {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-5);
  max-width: 520px;
  width: 100%;
}

.showcase-card {
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: box-shadow var(--transition), border-color var(--transition);
}

.showcase-card:hover {
  box-shadow: var(--shadow-2);
  border-color: var(--border-strong);
}

.showcase-card__info {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
}

.showcase-card__category {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.showcase-card__title {
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  color: var(--text);
  line-height: 1.3;
}

.showcase-card__price {
  font-size: var(--text-base);
  font-weight: var(--fw-semibold);
  color: var(--accent-text);
}

/* Responsive */
@media (max-width: 1100px) {
  .hero {
    grid-template-columns: 1fr;
    gap: var(--space-8);
    text-align: center;
  }

  .hero__content {
    max-width: 100%;
  }

  .hero__cta {
    justify-content: center;
  }
}

@media (max-width: 640px) {
  .hero {
    padding: var(--space-8) var(--space-4);
  }

  .hero__title {
    font-size: var(--text-xl);
  }

  .hero__subtitle {
    font-size: var(--text-base);
  }

  .hero__product-showcase {
    grid-template-columns: 1fr;
  }
}
</style>