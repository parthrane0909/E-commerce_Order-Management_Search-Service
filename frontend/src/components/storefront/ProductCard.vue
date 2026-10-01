<template>
  <article class="product-card">
    <ProductThumb :product="product" size="md" />

    <div class="product-card__body">
      <div class="product-card__meta">
        <span class="product-card__category">{{ product.category }}</span>
        <span class="product-card__price tabular">{{ formatCurrency(product.price) }}</span>
      </div>

      <h3 class="product-card__title truncate" :title="product.title">{{ product.title }}</h3>

      <p class="product-card__desc line-clamp-2">
        {{ product.description || 'No description available.' }}
      </p>

      <ul v-if="tags.length" class="product-card__tags">
        <li v-for="tag in visibleTags" :key="tag" class="tag-chip">{{ tag }}</li>
        <li v-if="overflowCount > 0" class="tag-chip tag-chip--more">+{{ overflowCount }}</li>
      </ul>

      <BaseButton
        class="product-card__cta"
        :variant="state === 'added' ? 'secondary' : 'primary'"
        :disabled="state === 'added'"
        @click="onAdd"
      >
        <AppIcon v-if="state === 'added'" name="check" :size="15" />
        {{ state === 'added' ? 'Added' : 'Add to cart' }}
      </BaseButton>
    </div>
  </article>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import BaseButton from '../common/BaseButton.vue'
import AppIcon from '../common/AppIcon.vue'
import ProductThumb from '../common/ProductThumb.vue'
import { formatCurrency } from '../../utils/currency'

const props = defineProps({
  product: { type: Object, required: true },
})

const emit = defineEmits(['add'])

const MAX_TAGS = 3
const RESET_AFTER = 1400

const state = ref('idle')
let timer = null

const tags = computed(() => (Array.isArray(props.product.tags) ? props.product.tags : []))
const visibleTags = computed(() => tags.value.slice(0, MAX_TAGS))
const overflowCount = computed(() => Math.max(0, tags.value.length - MAX_TAGS))

function onAdd() {
  if (state.value === 'added') return
  state.value = 'added'
  emit('add', props.product)
  clearTimeout(timer)
  timer = setTimeout(() => {
    state.value = 'idle'
  }, RESET_AFTER)
}

onBeforeUnmount(() => clearTimeout(timer))
</script>

<style scoped>
.product-card {
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-1);
  overflow: hidden;
  transition: box-shadow var(--transition), border-color var(--transition), transform var(--transition);
}

.product-card:hover {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-2);
  transform: translateY(-2px);
}

.product-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  flex: 1 1 auto;
}

.product-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.product-card__category {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.product-card__price {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text);
}

.product-card__title {
  font-size: var(--text-base);
  font-weight: 600;
  line-height: 1.3;
  color: var(--text);
}

.product-card__desc {
  font-size: var(--text-sm);
  color: var(--text-muted);
  line-height: 1.5;
  min-height: 44px;
}

.product-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  list-style: none;
  padding: 0;
  margin: 0;
}

.tag-chip {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--text-muted);
  font-weight: 500;
}

.tag-chip--more {
  background: var(--accent-soft);
  border-color: var(--accent-soft-border);
  color: var(--accent-text);
}

.product-card__cta {
  margin-top: auto;
  width: 100%;
}

/* Utility classes */
.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>