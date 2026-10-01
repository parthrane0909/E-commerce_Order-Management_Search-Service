<template>
  <AppCard class="success">
    <div class="success__body">
      <span class="success__icon">
        <AppIcon name="check" :size="26" />
      </span>

      <h2 class="success__title">Order placed</h2>
      <p class="success__lead">
        Thanks — your order was saved and is on its way to the search index.
      </p>

      <dl class="success__facts">
        <div class="success__fact">
          <dt>Order number</dt>
          <dd class="tabular">{{ order.order_number }}</dd>
        </div>
        <div class="success__fact">
          <dt>Total</dt>
          <dd class="tabular">{{ formatCurrency(order.total_amount) }}</dd>
        </div>
        <div class="success__fact">
          <dt>Status</dt>
          <dd><StatusBadge :status="order.status" /></dd>
        </div>
      </dl>

      <AppAlert :tone="syncTone" class="success__sync">
        <p class="medium" :class="syncTone === 'success' ? 'success__sync-title' : ''">
          {{ syncTitle }}
        </p>
        <p class="text-sm">{{ syncMessage }}</p>
      </AppAlert>

      <div class="success__actions">
        <BaseButton variant="primary" icon="external" @click="goToOrder">
          View order details
        </BaseButton>
        <BaseButton variant="secondary" icon="arrowLeft" @click="emit('continue')">
          Continue shopping
        </BaseButton>
      </div>
    </div>
  </AppCard>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppCard from '../common/AppCard.vue'
import AppAlert from '../common/AppAlert.vue'
import AppIcon from '../common/AppIcon.vue'
import BaseButton from '../common/BaseButton.vue'
import StatusBadge from '../common/StatusBadge.vue'
import { formatCurrency } from '../../utils/currency'

const props = defineProps({
  order: { type: Object, required: true },
})

const emit = defineEmits(['continue'])
const router = useRouter()

function goToOrder() {
  router.push({ name: 'order-details', params: { id: props.order.id } })
}

const enqueued = computed(() => props.order?.sync?.enqueued !== false)

const syncTone = computed(() => (enqueued.value ? 'success' : 'warning'))

const syncTitle = computed(() =>
  enqueued.value
    ? 'Queued for search synchronisation'
    : 'Warning: message queue unreachable',
)

const syncMessage = computed(() =>
  enqueued.value
    ? 'A RabbitMQ message was queued — Celery will index this order into Elasticsearch so it appears in the search dashboard.'
    : 'Could not reach the message queue — the order is still saved in PostgreSQL and will be indexed later.',
)
</script>

<style scoped>
.success__body {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--space-3);
  padding: var(--space-5) 0;
}

.success__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--success-soft);
  color: var(--success);
}

.success__title {
  font-size: var(--text-xl);
}

.success__lead {
  color: var(--text-muted);
  max-width: 460px;
}

.success__facts {
  display: flex;
  gap: var(--space-5);
  flex-wrap: wrap;
  justify-content: center;
  margin: var(--space-2) 0 0;
}

.success__fact {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.success__fact dt {
  font-size: var(--text-xs);
  font-weight: var(--fw-semibold);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-faint);
}

.success__fact dd {
  margin: 0;
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
}

.success__sync {
  text-align: left;
  max-width: 520px;
  width: 100%;
  flex-direction: column;
  gap: 2px;
}

.success__sync-title {
  color: inherit;
}

.success__actions {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
  justify-content: center;
  margin-top: var(--space-2);
}
</style>
