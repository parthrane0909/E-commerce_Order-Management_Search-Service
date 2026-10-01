const formatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const numberFormatter = new Intl.NumberFormat('en-US')

/** `$1,234.56` — returns an em dash for anything that is not a finite number. */
export function formatCurrency(value) {
  if (value === null || value === undefined || value === '') return '—'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return '—'
  return formatter.format(amount)
}

/** `1,234` */
export function formatNumber(value) {
  if (value === null || value === undefined || value === '') return '—'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return '—'
  return numberFormatter.format(amount)
}

/** Coerce form input to a positive money amount, or `null` when unusable. */
export function parseAmount(value) {
  if (value === '' || value === null || value === undefined) return null
  const amount = Number(value)
  if (!Number.isFinite(amount)) return null
  return amount
}
