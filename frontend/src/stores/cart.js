import { defineStore } from 'pinia'

export const MIN_QTY = 1
export const MAX_QTY = 100

function clampQty(qty) {
  const value = Math.floor(Number(qty))
  if (!Number.isFinite(value)) return MIN_QTY
  return Math.min(MAX_QTY, Math.max(MIN_QTY, value))
}

/**
 * Cart is keyed by product id and stores a title/price snapshot taken at add
 * time. The server re-prices everything when the order is placed.
 */
export const useCartStore = defineStore('cart', {
  state: () => ({
    /** @type {Record<string, {id: string, sku: string, title: string, price: number, category: string, image_url: string | null, quantity: number}>} */
    items: {},
  }),

  getters: {
    lines(state) {
      return Object.values(state.items)
    },

    isEmpty(state) {
      return Object.keys(state.items).length === 0
    },

    /** Total number of units across all lines. */
    itemCount() {
      return this.lines.reduce((sum, line) => sum + line.quantity, 0)
    },

    /** Snapshot subtotal — the server re-computes real prices at checkout. */
    subtotal() {
      return this.lines.reduce((sum, line) => sum + line.price * line.quantity, 0)
    },
  },

  actions: {
    /** Add a product (or increase its quantity). Returns the resulting line. */
    add(product, quantity = 1) {
      if (!product || !product.id) return null

      const existing = this.items[product.id]
      if (existing) {
        existing.quantity = clampQty(existing.quantity + quantity)
        return existing
      }

      const line = {
        id: product.id,
        sku: product.sku || '',
        title: product.title || 'Untitled product',
        price: Number(product.price) || 0,
        category: product.category || '',
        image_url: product.image_url || null,
        quantity: clampQty(quantity),
      }
      this.items[product.id] = line
      return line
    },

    /** Set a line's quantity, clamped to 1..100. */
    setQuantity(id, quantity) {
      const line = this.items[id]
      if (!line) return
      line.quantity = clampQty(quantity)
    },

    increment(id) {
      const line = this.items[id]
      if (line) line.quantity = clampQty(line.quantity + 1)
    },

    decrement(id) {
      const line = this.items[id]
      if (line) line.quantity = clampQty(line.quantity - 1)
    },

    remove(id) {
      delete this.items[id]
    },

    clear() {
      this.items = {}
    },
  },
})
