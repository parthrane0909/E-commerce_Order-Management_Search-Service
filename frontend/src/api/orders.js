import client from './client'

/**
 * Create an order. The server re-reads MongoDB and computes totals itself —
 * there is deliberately no price/total field in the request body.
 *
 * @param {{ user_id: number, items: Array<{ product_id: string, quantity: number }> }} payload
 */
export function createOrder(payload) {
  return client.post('/api/orders', payload)
}

/** Canonical order from PostgreSQL. */
export function getOrder(id) {
  return client.get(`/api/orders/${id}`)
}

/** Status update — PATCH /api/orders/{id}/status */
export function updateOrderStatus(id, status) {
  return client.patch(`/api/orders/${id}/status`, { status })
}
