<template>
  <div v-if="count > 1" class="skeleton-group" :class="`skeleton-group--${variant}`" aria-hidden="true">
    <span
      v-for="index in count"
      :key="index"
      class="skeleton"
      :class="`skeleton--${variant}`"
      :style="style"
    />
  </div>
  <span v-else class="skeleton" :class="`skeleton--${variant}`" :style="style" aria-hidden="true" />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** text | block | card | row | circle */
  variant: { type: String, default: 'block' },
  width: { type: [String, Number], default: null },
  height: { type: [String, Number], default: null },
  /** Render `count` skeletons in a responsive grid. */
  count: { type: Number, default: 1 },
})

const style = computed(() => {
  const styles = {}
  if (props.width !== null) styles.width = typeof props.width === 'number' ? `${props.width}px` : props.width
  if (props.height !== null) {
    styles.height = typeof props.height === 'number' ? `${props.height}px` : props.height
  }
  return styles
})
</script>

<style scoped>
.skeleton {
  display: block;
  background: linear-gradient(
    90deg,
    var(--surface-3) 25%,
    var(--surface-2) 37%,
    var(--surface-3) 63%
  );
  background-size: 400% 100%;
  animation: skeleton-shimmer 1.4s ease infinite;
  border-radius: var(--radius-sm);
}

.skeleton--text {
  height: 12px;
  width: 100%;
  border-radius: 999px;
}

.skeleton--block {
  height: 16px;
  width: 100%;
}

.skeleton--circle {
  border-radius: 50%;
  width: 40px;
  height: 40px;
}

.skeleton--row {
  height: 52px;
  width: 100%;
  border-radius: var(--radius-sm);
}

.skeleton--card {
  height: 268px;
  width: 100%;
  border-radius: var(--radius);
}

.skeleton-group {
  display: grid;
  gap: var(--space-4);
}

.skeleton-group--card {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.skeleton-group--row {
  gap: var(--space-2);
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

@media (max-width: 1100px) {
  .skeleton-group--card {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .skeleton-group--card {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .skeleton-group--card {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
