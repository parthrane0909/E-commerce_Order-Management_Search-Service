<template>
  <section
    v-if="tags.length"
    class="marquee"
    :class="{ 'marquee--static': useStatic }"
    aria-labelledby="marquee-heading"
  >
    <div class="marquee__head">
      <h2 id="marquee-heading" class="marquee__label">
        <span class="marquee__dot" aria-hidden="true" />
        Trending now
      </h2>
      <span class="marquee__hint">{{ hint }}</span>
    </div>

    <!-- Animated: one continuous right-to-left line -->
    <div
      v-if="!useStatic"
      class="marquee__viewport"
      @mouseenter="paused = true"
      @mouseleave="paused = false"
      @touchstart="paused = true"
      @touchend="paused = false"
      @touchcancel="paused = false"
    >
      <div
        class="marquee__track"
        :class="{ 'marquee__track--paused': paused }"
        :style="{ animationDuration: `${duration}s` }"
      >
        <div v-for="copy in 2" :key="copy" class="marquee__group" :aria-hidden="copy === 2">
          <TagPill
            v-for="tag in tags"
            :key="`${copy}-${tag.value}`"
            :tag="tag"
            :clickable="clickable"
            class="marquee__item"
          />
        </div>
      </div>
    </div>

    <!-- Reduced motion: static, horizontally scrollable, scrollbar hidden -->
    <div v-else class="marquee__viewport marquee__viewport--static" role="list">
      <TagPill
        v-for="tag in tags"
        :key="tag.value"
        :tag="tag"
        :clickable="clickable"
        role="listitem"
        class="marquee__item"
      />
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import TagPill from './TagPill.vue'

const props = defineProps({
  tags: { type: Array, default: () => [] },
  clickable: { type: Boolean, default: true },
  /** pixels of travel per second */
  speed: { type: Number, default: 70 },
})

const paused = ref(false)
const useStatic = ref(false)
let mediaQuery = null

const hint = computed(() =>
  props.clickable ? 'Tap a tag to search' : 'Popular across the catalog',
)

/**
 * The track holds two identical groups, so translating it by -50% returns to
 * the exact starting frame (each pill carries its own right margin, which is
 * what makes the period match). Duration is derived from the real width so the
 * scroll speed stays constant no matter how many tags arrive.
 */
const duration = computed(() => {
  const count = Math.max(props.tags.length, 1)
  // ~150px average pill incl. gap, two groups, at `speed` px/s.
  const distance = (count * 150 * 2) / props.speed
  return Math.max(Math.round(distance), 18)
})

function applyMotionPreference(event) {
  useStatic.value = Boolean(event?.matches)
}

onMounted(() => {
  if (typeof window !== 'undefined' && window.matchMedia) {
    mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    applyMotionPreference(mediaQuery)
    mediaQuery.addEventListener?.('change', applyMotionPreference)
  }
})

onBeforeUnmount(() => {
  mediaQuery?.removeEventListener?.('change', applyMotionPreference)
})
</script>

<style scoped>
.marquee {
  width: 100%;
  min-width: 0;
  margin-bottom: var(--space-8);
  overflow: hidden;
}

.marquee__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.marquee__label {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0;
  font-size: var(--text-2xl);
  line-height: 1.2;
  font-weight: var(--fw-bold);
  letter-spacing: -0.02em;
  color: var(--color-text);
}

.marquee__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary);
  box-shadow: 0 0 0 4px var(--color-primary-soft);
}

.marquee__hint {
  font-size: var(--text-sm);
  color: var(--color-text-faint);
  white-space: nowrap;
}

/* ---------------- viewport / track ---------------- */

.marquee__viewport {
  position: relative;
  width: 100%;
  overflow-x: hidden;
  padding: var(--space-1) 0;
  -webkit-mask-image: linear-gradient(
    to right,
    transparent 0,
    #000 40px,
    #000 calc(100% - 40px),
    transparent 100%
  );
  mask-image: linear-gradient(
    to right,
    transparent 0,
    #000 40px,
    #000 calc(100% - 40px),
    transparent 100%
  );
}

.marquee__viewport--static {
  display: flex;
  flex-wrap: nowrap;
  overflow-x: auto;
  scroll-snap-type: x proximity;
  scrollbar-width: none;
  -ms-overflow-style: none;
  -webkit-mask-image: none;
  mask-image: none;
}

.marquee__viewport--static::-webkit-scrollbar {
  display: none;
}

.marquee__track {
  display: flex;
  flex-wrap: nowrap;
  width: max-content;
  will-change: transform;
  animation-name: marquee-slide;
  animation-timing-function: linear;
  animation-iteration-count: infinite;
}

.marquee__track--paused {
  animation-play-state: paused;
}

.marquee__group {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
}

/* Margin (not container gap) keeps the loop period exactly 50% of the track. */
.marquee__item {
  margin-right: var(--space-3);
  scroll-snap-align: start;
}

.marquee__group .marquee__item:last-child {
  margin-right: var(--space-3);
}

@keyframes marquee-slide {
  from {
    transform: translate3d(0, 0, 0);
  }
  to {
    transform: translate3d(-50%, 0, 0);
  }
}

/* ---------------- responsive ---------------- */

@media (max-width: 640px) {
  .marquee {
    margin-bottom: var(--space-6);
  }

  .marquee__label {
    font-size: var(--text-xl);
  }

  .marquee__hint {
    display: none;
  }

  .marquee__viewport {
    -webkit-mask-image: none;
    mask-image: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .marquee__track {
    animation: none !important;
    transform: none !important;
  }
}
</style>
