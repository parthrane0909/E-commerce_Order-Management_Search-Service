<template>
  <button
    v-if="clickable"
    type="button"
    class="tag-pill tag-pill--clickable"
    :aria-label="`Search for ${formatTag(tag.value)}`"
    @click="onClick"
  >
    <span class="tag-pill__hash" aria-hidden="true">#</span>
    <span class="tag-pill__text">{{ formatTag(tag.value) }}</span>
  </button>
  <span v-else class="tag-pill">
    <span class="tag-pill__hash" aria-hidden="true">#</span>
    <span class="tag-pill__text">{{ formatTag(tag.value) }}</span>
  </span>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  tag: { type: Object, required: true },
  clickable: { type: Boolean, default: false },
})

const route = useRoute()
const router = useRouter()

function formatTag(value) {
  const raw = String(value || '')
  return raw.charAt(0).toUpperCase() + raw.slice(1)
}

/** A trending tag runs the global search — no filter panel in between. */
function onClick() {
  if (!props.clickable) return
  const query = { ...route.query }
  query.q = String(props.tag.value || '')
  delete query.page
  delete query.category
  router.replace({ query }).catch(() => {})
}
</script>

<style scoped>
.tag-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex: none;
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  background: var(--color-surface);
  color: var(--color-text);
  font-size: var(--text-sm);
  font-weight: var(--fw-medium);
  white-space: nowrap;
  line-height: 1.25;
  transition:
    border-color var(--transition),
    background-color var(--transition),
    color var(--transition),
    box-shadow var(--transition);
}

.tag-pill--clickable {
  cursor: pointer;
}

.tag-pill:hover {
  border-color: var(--color-ink);
  background: var(--color-ink);
  color: var(--color-primary);
}

.tag-pill:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
  border-color: var(--color-primary);
}

.tag-pill__hash {
  color: var(--color-primary-hover);
  font-weight: var(--fw-bold);
}

.tag-pill:hover .tag-pill__hash {
  color: var(--color-primary);
}

.tag-pill__text {
  line-height: 1.25;
}

@media (prefers-reduced-motion: reduce) {
  .tag-pill {
    transition: none;
  }
}
</style>
