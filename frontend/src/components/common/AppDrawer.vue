<template>
  <Teleport to="body">
    <Transition name="drawer-fade">
      <div v-if="open" class="drawer-backdrop" @mousedown.self="emit('close')">
        <aside
          class="drawer"
          :style="{ width }"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          @keydown.esc.stop="emit('close')"
        >
          <header class="drawer__header">
            <h2 :id="titleId" class="drawer__title">
              <slot name="title">{{ title }}</slot>
            </h2>
            <button
              type="button"
              class="drawer__close"
              aria-label="Close drawer"
              @click="emit('close')"
            >
              <AppIcon name="close" :size="18" />
            </button>
          </header>

          <div ref="body" class="drawer__body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="drawer__footer">
            <slot name="footer" />
          </footer>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, watch } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  open: Boolean,
  title: { type: String, default: '' },
  width: { type: String, default: '420px' },
})

const emit = defineEmits(['close'])

const titleId = `drawer-title-${Math.random().toString(36).slice(2, 9)}`

function onKeydown(event) {
  if (event.key === 'Escape') emit('close')
}

watch(
  () => props.open,
  (open) => {
    document.body.style.overflow = open ? 'hidden' : ''
    if (open) window.addEventListener('keydown', onKeydown)
    else window.removeEventListener('keydown', onKeydown)
  },
)

onBeforeUnmount(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKeydown)
})
</script>

<style scoped>
.drawer-backdrop {
  position: fixed;
  inset: 0;
  z-index: 55;
  background: rgba(18, 22, 29, 0.45);
}

.drawer {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  max-width: 100vw;
  background: var(--surface);
  box-shadow: var(--shadow-2);
  display: flex;
  flex-direction: column;
}

.drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--border);
}

.drawer__title {
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
}

.drawer__close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: background-color var(--transition), color var(--transition);
}

.drawer__close:hover {
  background: var(--surface-2);
  color: var(--text);
}

.drawer__body {
  flex: 1 1 auto;
  overflow-y: auto;
  padding: var(--space-4) var(--space-5);
}

.drawer__footer {
  border-top: 1px solid var(--border);
  background: var(--surface-2);
  padding: var(--space-4) var(--space-5);
}

.drawer-fade-enter-active,
.drawer-fade-leave-active {
  transition: opacity var(--transition);
}

.drawer-fade-enter-active .drawer,
.drawer-fade-leave-active .drawer {
  transition: transform var(--transition);
}

.drawer-fade-enter-from,
.drawer-fade-leave-to {
  opacity: 0;
}

.drawer-fade-enter-from .drawer,
.drawer-fade-leave-to .drawer {
  transform: translateX(24px);
}
</style>
