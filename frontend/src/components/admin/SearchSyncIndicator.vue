<template>
  <div class="sync" :class="indexed ? 'sync--on' : 'sync--pending'">
    <span class="sync__dot" aria-hidden="true" />
    <span class="sync__label">{{ indexed ? 'Indexed' : 'Not yet indexed' }}</span>

    <span class="sync__info" tabindex="0" aria-label="About search synchronisation">
      <AppIcon name="info" :size="14" />
      <span class="sync__tooltip" role="tooltip">
        <strong>How search sync works</strong>
        The order is saved in PostgreSQL, published to RabbitMQ, then Celery consumes the message and
        indexes the document into Elasticsearch.
        <template v-if="indexed">Indexed at {{ formatDateTime(indexedAt) }} (UTC).</template>
        <template v-else>
          This order has not been indexed yet — indexing normally completes within a few seconds.
        </template>
      </span>
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import AppIcon from '../common/AppIcon.vue'
import { formatDateTime } from '../../utils/dates'

const props = defineProps({
  indexedAt: { type: String, default: null },
})

const indexed = computed(() => Boolean(props.indexedAt))
</script>

<style scoped>
.sync {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 6px 10px;
  border-radius: 999px;
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  border: 1px solid transparent;
}

.sync--on {
  background: var(--success-soft);
  border-color: var(--success-border);
  color: var(--success);
}

.sync--pending {
  background: var(--warning-soft);
  border-color: var(--warning-border);
  color: var(--warning);
}

.sync__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.sync__info {
  position: relative;
  display: inline-flex;
  align-items: center;
  color: inherit;
  cursor: help;
}

.sync__tooltip {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 20;
  width: 260px;
  padding: var(--space-3);
  background: var(--text);
  color: var(--inverse);
  font-size: var(--text-xs);
  font-weight: 400;
  line-height: var(--lh-base);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-2);
  opacity: 0;
  visibility: hidden;
  transform: translateY(-4px);
  transition: opacity var(--transition), transform var(--transition), visibility var(--transition);
  text-align: left;
}

.sync__tooltip strong {
  display: block;
  margin-bottom: 4px;
  font-weight: var(--fw-semibold);
}

.sync__info:hover .sync__tooltip,
.sync__info:focus-visible .sync__tooltip {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}
</style>
