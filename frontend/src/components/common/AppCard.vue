<template>
  <section class="card" :class="{ 'card--flush': flush }">
    <header
      v-if="title || subtitle || $slots.aside || $slots.subtitle"
      class="card__header"
    >
      <div class="card__titles">
        <h2 v-if="title" class="card__title">{{ title }}</h2>
        <p v-if="subtitle" class="card__subtitle">{{ subtitle }}</p>
        <slot name="subtitle" />
      </div>
      <div v-if="$slots.aside" class="card__aside">
        <slot name="aside" />
      </div>
    </header>

    <div class="card__body">
      <slot />
    </div>

    <footer v-if="$slots.footer" class="card__footer">
      <slot name="footer" />
    </footer>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  /** Remove body padding (tables manage their own). */
  flush: Boolean,
})
</script>

<style scoped>
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-1);
  overflow: hidden;
}

.card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--border);
}

.card__title {
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
}

.card__subtitle,
.card__titles :deep(.card__subtitle) {
  margin-top: 2px;
  font-size: var(--text-sm);
  color: var(--text-muted);
}

.card__aside {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex: none;
}

.card__body {
  padding: var(--space-5);
}

.card--flush .card__body {
  padding: 0;
}

.card__footer {
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--border);
  background: var(--surface-2);
}
</style>
