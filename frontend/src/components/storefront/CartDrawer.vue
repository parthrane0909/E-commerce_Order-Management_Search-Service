<template>
  <AppDrawer :open="open" title="Your cart" width="440px" @close="emit('close')">
    <template #title>
      Your cart
      <span v-if="cart.itemCount" class="muted text-sm"> · {{ cart.itemCount }} items</span>
    </template>

    <EmptyState
      v-if="cart.isEmpty"
      icon="bag"
      title="Your cart is empty"
      message="Add products from the catalog to start an order."
    >
      <template #actions>
        <BaseButton variant="secondary" @click="emit('close')">Browse products</BaseButton>
      </template>
    </EmptyState>

    <ul v-else class="cart-lines">
      <li v-for="line in cart.lines" :key="line.id" class="cart-line">
        <ProductThumb :product="line" size="sm" />

        <div class="cart-line__info">
          <p class="cart-line__title truncate" :title="line.title">{{ line.title }}</p>
          <p class="cart-line__meta text-xs muted">
            <span v-if="line.sku">{{ line.sku }} · </span>
            <span class="tabular">{{ formatCurrency(line.price) }}</span> each
          </p>

          <div class="cart-line__controls">
            <div class="qty">
              <button
                type="button"
                class="qty__btn"
                aria-label="Decrease quantity"
                :disabled="line.quantity <= 1"
                @click="cart.decrement(line.id)"
              >
                <AppIcon name="minus" :size="13" />
              </button>
              <input
                class="qty__input tabular"
                type="number"
                min="1"
                max="100"
                :value="line.quantity"
                :aria-label="`Quantity for ${line.title}`"
                @change="onQuantityChange(line.id, $event)"
              />
              <button
                type="button"
                class="qty__btn"
                aria-label="Increase quantity"
                :disabled="line.quantity >= 100"
                @click="cart.increment(line.id)"
              >
                <AppIcon name="plus" :size="13" />
              </button>
            </div>

            <button
              type="button"
              class="cart-line__remove"
              :aria-label="`Remove ${line.title} from cart`"
              @click="cart.remove(line.id)"
            >
              <AppIcon name="trash" :size="15" />
            </button>
          </div>
        </div>

        <span class="cart-line__total tabular">{{ formatCurrency(line.price * line.quantity) }}</span>
      </li>
    </ul>

    <template v-if="!cart.isEmpty" #footer>
      <div class="cart-summary">
        <div class="row-between">
          <span class="muted">Subtotal</span>
          <span class="cart-summary__total tabular">{{ formatCurrency(cart.subtotal) }}</span>
        </div>
        <p class="text-xs faint">
          Prices are re-read from the catalog and re-confirmed by the server at checkout.
        </p>
        <BaseButton block @click="emit('checkout')">Proceed to checkout</BaseButton>
      </div>
    </template>
  </AppDrawer>
</template>

<script setup>
import AppDrawer from '../common/AppDrawer.vue'
import EmptyState from '../common/EmptyState.vue'
import BaseButton from '../common/BaseButton.vue'
import AppIcon from '../common/AppIcon.vue'
import ProductThumb from '../common/ProductThumb.vue'
import { useCartStore } from '../../stores/cart'
import { formatCurrency } from '../../utils/currency'

defineProps({
  open: Boolean,
})

const emit = defineEmits(['close', 'checkout'])
const cart = useCartStore()

function onQuantityChange(id, event) {
  cart.setQuantity(id, Number(event.target.value))
}
</script>

<style scoped>
.cart-lines {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.cart-line {
  display: flex;
  gap: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border);
}

.cart-line:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.cart-line__info {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.cart-line__title {
  font-size: var(--text-base);
  font-weight: var(--fw-medium);
}

.cart-line__controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-top: var(--space-1);
}

.qty {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.qty__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 0;
  background: var(--surface-2);
  color: var(--text-muted);
  cursor: pointer;
}

.qty__btn:hover:not(:disabled) {
  background: var(--surface-3);
  color: var(--text);
}

.qty__btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.qty__input {
  width: 44px;
  height: 28px;
  border: 0;
  border-left: 1px solid var(--border);
  border-right: 1px solid var(--border);
  text-align: center;
  font-size: var(--text-sm);
  background: var(--surface);
  -moz-appearance: textfield;
  appearance: textfield;
}

.qty__input::-webkit-outer-spin-button,
.qty__input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.cart-line__remove {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-faint);
  cursor: pointer;
  transition: background-color var(--transition), color var(--transition);
}

.cart-line__remove:hover {
  background: var(--danger-soft);
  color: var(--danger);
}

.cart-line__total {
  font-weight: var(--fw-semibold);
  white-space: nowrap;
  align-self: flex-start;
  padding-top: 2px;
}

.cart-summary {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.cart-summary__total {
  font-size: var(--text-lg);
  font-weight: var(--fw-semibold);
}
</style>
