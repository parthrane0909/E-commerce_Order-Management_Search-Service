<template>
  <div
    class="thumb"
    :class="[
      `thumb--${size}`,
      {
        'thumb--has-image': showImage,
        'thumb--loading': loading,
        'thumb--error': failed,
      },
    ]"
    role="img"
    :aria-label="`${product.title} preview`"
  >
    <img
      v-if="showImage"
      :src="imageUrl"
      :alt="product.title"
      class="thumb__image"
      loading="lazy"
      decoding="async"
      @load="onLoad"
      @error="onError"
    />
    <div v-else class="thumb__placeholder">
      <span class="thumb__monogram">{{ monogram }}</span>
      <span class="thumb__pattern" :class="`thumb__pattern--${patternIndex}`" aria-hidden="true" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { resolveImageUrl } from '../../utils/image'

const props = defineProps({
  product: { type: Object, required: true },
  size: { type: String, default: 'md' },
})

const loading = ref(false)
const failed = ref(false)

const imageUrl = computed(() => resolveImageUrl(props.product?.image_url))

/** A missing image AND a failed load both fall back to the branded placeholder. */
const showImage = computed(() => Boolean(imageUrl.value) && !failed.value)

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

function onLoad() {
  loading.value = false
  failed.value = false
}

function onError() {
  loading.value = false
  failed.value = true
}

watch(
  imageUrl,
  (value) => {
    failed.value = false
    loading.value = Boolean(value)
  },
  { immediate: true },
)
</script>

<style scoped>
.thumb {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary-soft);
  color: var(--color-primary-hover);
  border-radius: var(--radius-sm);
  overflow: hidden;
  flex: none;
  user-select: none;
}

.thumb__image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  border-radius: inherit;
}

.thumb__placeholder {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  gap: var(--space-1);
  overflow: hidden;
}

.thumb__monogram {
  position: relative;
  z-index: 1;
  font-weight: var(--fw-bold);
  letter-spacing: 0.06em;
  color: var(--color-primary-hover);
  opacity: 0.9;
}

.thumb__pattern {
  position: absolute;
  inset: 0;
  opacity: 0.55;
  pointer-events: none;
}

.thumb__pattern--1 {
  background-image: radial-gradient(var(--color-primary-border) 1.2px, transparent 1.2px);
  background-size: 10px 10px;
}

.thumb__pattern--2 {
  background-image: repeating-linear-gradient(
    -45deg,
    transparent 0 7px,
    var(--color-primary-border) 7px 8px
  );
}

.thumb__pattern--3 {
  background-image: repeating-linear-gradient(
    transparent 0 8px,
    var(--color-primary-border) 8px 9px
  );
}

.thumb__pattern--4 {
  background-image: linear-gradient(
    135deg,
    var(--color-primary-soft) 0 60%,
    var(--color-primary-border) 60%
  );
}

.thumb--sm {
  width: 44px;
  height: 44px;
  font-size: var(--text-sm);
}

.thumb--md {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 0;
  font-size: var(--text-xl);
}

.thumb--lg {
  width: 64px;
  height: 64px;
  font-size: var(--text-md);
}

@media (prefers-reduced-motion: reduce) {
  .thumb__image {
    transition: none;
  }
}
</style>
