<template>
  <div
    class="thumb"
    :class="[`thumb--${size}`, `thumb--pattern-${patternIndex}`]"
    role="img"
    :aria-label="`${product.title} preview`"
  >
    <span class="thumb__monogram">{{ monogram }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  product: { type: Object, required: true },
  size: { type: String, default: 'md' },
})

/** Deterministic pattern chosen from the product title (no external images). */
const patternIndex = computed(() => {
  const title = props.product?.title || ''
  let hash = 0
  for (let i = 0; i < title.length; i += 1) {
    hash = (hash * 31 + title.charCodeAt(i)) % 997
  }
  return (hash % 4) + 1
})

/** First letters of the first two words (or the first two characters). */
const monogram = computed(() => {
  const words = String(props.product?.title || '')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
  if (!words.length) return '?'
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  return (words[0][0] + words[1][0]).toUpperCase()
})
</script>

<style scoped>
.thumb {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-soft);
  color: var(--accent-text);
  border-radius: var(--radius-sm);
  overflow: hidden;
  flex: none;
  user-select: none;
}

.thumb__monogram {
  font-weight: var(--fw-semibold);
  letter-spacing: 0.02em;
  position: relative;
  z-index: 1;
}

/* Subtle category-free patterns derived from the title hash. */
.thumb--pattern-1 {
  background-image: radial-gradient(var(--accent-soft-border) 1px, transparent 1px);
  background-size: 8px 8px;
}

.thumb--pattern-2 {
  background-image: repeating-linear-gradient(
    -45deg,
    transparent 0 6px,
    var(--accent-soft-border) 6px 7px
  );
}

.thumb--pattern-3 {
  background-image: repeating-linear-gradient(
    transparent 0 7px,
    var(--accent-soft-border) 7px 8px
  );
}

.thumb--pattern-4 {
  background-image: linear-gradient(135deg, var(--accent-soft) 0 60%, var(--accent-soft-border) 60%);
}

.thumb--sm {
  width: 40px;
  height: 40px;
  font-size: var(--text-sm);
}

.thumb--md {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: var(--radius) var(--radius) 0 0;
  font-size: var(--text-xl);
}

.thumb--lg {
  width: 64px;
  height: 64px;
  font-size: var(--text-md);
}
</style>
