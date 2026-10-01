<template>
  <AppCard title="Order summary" class="summary">
    <dl class="summary__rows">
      <div class="summary__row">
        <dt>Items</dt>
        <dd class="tabular">{{ itemCount }}</dd>
      </div>
      <div class="summary__row">
        <dt>Subtotal</dt>
        <dd class="tabular">{{ formatCurrency(subtotal) }}</dd>
      </div>
      <div class="summary__row summary__row--total">
        <dt>Total</dt>
        <dd class="tabular">{{ formatCurrency(subtotal) }}</dd>
      </div>
    </dl>

    <div class="summary__customer">
      <p class="summary__label">Customer</p>
      <template v-if="customer">
        <p class="summary__customer-name">{{ customer.name }}</p>
        <p class="text-sm muted truncate">{{ customer.email }}</p>
      </template>
      <p v-else class="text-sm muted">No customer selected</p>
    </div>

    <BaseButton block :loading="placing" :disabled="disabled" @click="emit('place')">
      Place order
    </BaseButton>

    <p v-if="disabledReason" class="summary__reason">{{ disabledReason }}</p>

    <p class="summary__note">
      The server re-reads every price from MongoDB and computes the total itself — you never send
      amounts to the API.
    </p>
  </AppCard>
</template>

<script setup>
import AppCard from '../common/AppCard.vue'
import BaseButton from '../common/BaseButton.vue'
import { formatCurrency } from '../../utils/currency'

defineProps({
  itemCount: { type: Number, default: 0 },
  subtotal: { type: Number, default: 0 },
  customer: { type: Object, default: null },
  placing: Boolean,
  disabled: Boolean,
  disabledReason: { type: String, default: '' },
})

const emit = defineEmits(['place'])
</script>

<style scoped>
.summary {
  position: sticky;
  top: calc(var(--topbar-h) + var(--space-4));
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.summary__rows {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.summary__row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  font-size: var(--text-base);
  color: var(--text-muted);
}

.summary__row dd {
  margin: 0;
  color: var(--text);
}

.summary__row--total {
  padding-top: var(--space-3);
  border-top: 1px solid var(--border);
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
}

.summary__row--total dt,
.summary__row--total dd {
  color: var(--text);
  font-size: var(--text-lg);
}

.summary__customer {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-3);
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.summary__label {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.summary__customer-name {
  font-weight: var(--fw-medium);
}

.summary__reason {
  font-size: var(--text-sm);
  color: var(--warning);
}

.summary__note {
  font-size: var(--text-xs);
  color: var(--text-faint);
  line-height: var(--lh-base);
}
</style>
