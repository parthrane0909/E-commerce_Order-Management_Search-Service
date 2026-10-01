<template>
  <Teleport to="body">
    <Transition name="modal-fade">
      <div v-if="open" class="modal-backdrop" @mousedown.self="onBackdrop">
        <div
          ref="dialog"
          class="modal"
          :class="`modal--${size}`"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
          tabindex="-1"
          @keydown="onKeydown"
        >
          <header class="modal__header">
            <h2 :id="titleId" class="modal__title">
              <slot name="title">{{ title }}</slot>
            </h2>
            <button
              v-if="!hideClose"
              type="button"
              class="modal__close"
              aria-label="Close dialog"
              @click="emit('close')"
            >
              <AppIcon name="close" :size="18" />
            </button>
          </header>

          <div class="modal__body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="modal__footer">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import AppIcon from './AppIcon.vue'

const props = defineProps({
  open: Boolean,
  title: { type: String, default: '' },
  size: { type: String, default: 'md' },
  hideClose: Boolean,
  closeOnBackdrop: { type: Boolean, default: true },
})

const emit = defineEmits(['close'])

const dialog = ref(null)
const titleId = `modal-title-${Math.random().toString(36).slice(2, 9)}`
let previouslyFocused = null

function focusableElements() {
  if (!dialog.value) return []
  return Array.from(
    dialog.value.querySelectorAll(
      'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
    ),
  ).filter((el) => el.offsetParent !== null || el === document.activeElement)
}

function onKeydown(event) {
  if (event.key === 'Escape') {
    event.stopPropagation()
    emit('close')
    return
  }

  // Lightweight focus trap so keyboard users stay inside the dialog.
  if (event.key === 'Tab') {
    const elements = focusableElements()
    if (!elements.length) return
    const first = elements[0]
    const last = elements[elements.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }
}

function onBackdrop() {
  if (props.closeOnBackdrop) emit('close')
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      previouslyFocused = document.activeElement
      document.body.style.overflow = 'hidden'
      await nextTick()
      const elements = focusableElements()
      ;(elements[0] || dialog.value)?.focus()
    } else {
      document.body.style.overflow = ''
      if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
        previouslyFocused.focus()
      }
      previouslyFocused = null
    }
  },
)

onBeforeUnmount(() => {
  document.body.style.overflow = ''
})
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: rgba(18, 22, 29, 0.5);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: var(--space-6) var(--space-4);
  overflow-y: auto;
}

.modal {
  background: var(--surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-2);
  width: 100%;
  max-width: 560px;
  margin: auto;
  outline: none;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - var(--space-8));
}

.modal--sm {
  max-width: 420px;
}

.modal--lg {
  max-width: 760px;
}

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--border);
}

.modal__title {
  font-size: var(--text-md);
  font-weight: var(--fw-semibold);
}

.modal__close {
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

.modal__close:hover {
  background: var(--surface-2);
  color: var(--text);
}

.modal__body {
  padding: var(--space-5);
  overflow-y: auto;
}

.modal__footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--border);
  background: var(--surface-2);
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity var(--transition);
}

.modal-fade-enter-active .modal,
.modal-fade-leave-active .modal {
  transition: transform var(--transition);
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-from .modal,
.modal-fade-leave-to .modal {
  transform: translateY(8px);
}

@media (max-width: 640px) {
  .modal {
    max-width: none;
  }

  .modal__footer {
    flex-direction: column-reverse;
    align-items: stretch;
  }
}
</style>
