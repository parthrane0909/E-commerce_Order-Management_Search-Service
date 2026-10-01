import { describe, it, expect, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useCartStore, MAX_QTY } from '../src/stores/cart'

function makeProduct(overrides = {}) {
  return {
    id: 'prod-1',
    sku: 'ORG-001',
    title: 'Desk Organizer Bamboo',
    price: 27.5,
    category: 'office',
    ...overrides,
  }
}

describe('cart store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('adds a product once and snapshots title/price', () => {
    const cart = useCartStore()
    cart.add(makeProduct())

    expect(cart.lines).toHaveLength(1)
    expect(cart.isEmpty).toBe(false)
    expect(cart.lines[0]).toMatchObject({
      id: 'prod-1',
      title: 'Desk Organizer Bamboo',
      price: 27.5,
      quantity: 1,
    })
    expect(cart.itemCount).toBe(1)
  })

  it('merges repeat adds into the same line instead of duplicating it', () => {
    const cart = useCartStore()
    cart.add(makeProduct())
    cart.add(makeProduct(), 2)

    expect(cart.lines).toHaveLength(1)
    expect(cart.lines[0].quantity).toBe(3)
    expect(cart.itemCount).toBe(3)
  })

  it('clamps quantities to the 1..100 range', () => {
    const cart = useCartStore()
    cart.add(makeProduct())

    cart.setQuantity('prod-1', 999)
    expect(cart.lines[0].quantity).toBe(MAX_QTY)

    cart.setQuantity('prod-1', -5)
    expect(cart.lines[0].quantity).toBe(1)

    cart.setQuantity('prod-1', 7)
    expect(cart.lines[0].quantity).toBe(7)

    cart.setQuantity('prod-1', Number.NaN)
    expect(cart.lines[0].quantity).toBe(1)
  })

  it('computes subtotal across multiple lines', () => {
    const cart = useCartStore()
    cart.add(makeProduct({ id: 'a', price: 10 }))
    cart.add(makeProduct({ id: 'b', price: 12.5 }), 2)
    cart.add(makeProduct({ id: 'c', price: 3.33 }), 3)

    // 10 * 1 + 12.5 * 2 + 3.33 * 3 = 44.99
    expect(cart.subtotal).toBeCloseTo(44.99, 2)
    expect(cart.itemCount).toBe(6)
  })

  it('removes lines and clears the cart', () => {
    const cart = useCartStore()
    cart.add(makeProduct({ id: 'a' }))
    cart.add(makeProduct({ id: 'b' }))

    cart.remove('a')
    expect(cart.lines).toHaveLength(1)
    expect(cart.lines[0].id).toBe('b')

    cart.clear()
    expect(cart.isEmpty).toBe(true)
    expect(cart.subtotal).toBe(0)
  })

  it('ignores products without an id', () => {
    const cart = useCartStore()
    expect(cart.add({ title: 'No id', price: 5 })).toBeNull()
    expect(cart.isEmpty).toBe(true)
  })
})
