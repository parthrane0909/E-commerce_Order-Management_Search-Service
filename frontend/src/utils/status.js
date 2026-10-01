/** Order status helpers shared by badges, selects, filters and tests. */

export const ORDER_STATUSES = ['PENDING', 'PROCESSING', 'SHIPPED']

const LABELS = {
  PENDING: 'Pending',
  PROCESSING: 'Processing',
  SHIPPED: 'Shipped',
}

const TONES = {
  PENDING: 'warning',
  PROCESSING: 'info',
  SHIPPED: 'success',
}

export function isOrderStatus(value) {
  return ORDER_STATUSES.includes(value)
}

/** `PENDING` -> `Pending` (unknown values are passed through). */
export function statusLabel(status) {
  if (!status) return 'Unknown'
  return LABELS[status] || String(status).toLowerCase().replace(/^./, (c) => c.toUpperCase())
}

/** Map a status onto the design-system tone used by AppBadge. */
export function statusTone(status) {
  return TONES[status] || 'neutral'
}

/** Options list for BaseSelect (`[{ value, label }]`). */
export function statusOptions() {
  return ORDER_STATUSES.map((value) => ({ value, label: statusLabel(value) }))
}
