import { defineStore } from 'pinia'

let nextId = 1

/** Toast queue rendered by ToastHost (no alert()/confirm() anywhere). */
export const useToastStore = defineStore('toast', {
  state: () => ({
    /** @type {Array<{id: number, type: string, message: string, timeout: number}>} */
    toasts: [],
  }),

  actions: {
    push(type, message, timeout = 4500) {
      const toast = { id: nextId++, type, message, timeout }
      this.toasts.push(toast)
      // Keep the queue short so old messages never pile up.
      if (this.toasts.length > 5) this.toasts.splice(0, this.toasts.length - 5)
      return toast.id
    },

    success(message, timeout) {
      return this.push('success', message, timeout)
    },

    error(message, timeout) {
      return this.push('error', message, timeout || 6500)
    },

    info(message, timeout) {
      return this.push('info', message, timeout)
    },

    warning(message, timeout) {
      return this.push('warning', message, timeout || 6500)
    },

    dismiss(id) {
      const index = this.toasts.findIndex((toast) => toast.id === id)
      if (index !== -1) this.toasts.splice(index, 1)
    },
  },
})
