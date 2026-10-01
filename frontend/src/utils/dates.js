/**
 * Date helpers.
 *
 * The API returns naive UTC timestamps ("2026-09-29T11:12:47.221000") as well
 * as timezone-aware ones ("…Z"). Everything is rendered as UTC so the demo
 * never shifts times depending on the viewer's locale.
 *
 * Formatting is deliberately hand-rolled (no Intl locale drift) so output is
 * stable across machines and test environments.
 */

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

function pad(value) {
  return String(value).padStart(2, '0')
}

/** Parse any API timestamp into a Date, treating naive values as UTC. */
export function toUtcDate(value) {
  if (!value) return null
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value

  let raw = String(value).trim()
  if (!raw) return null

  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(raw)
  if (!hasZone) raw = `${raw}Z`
  // JS only honours 3 fractional digits; truncate microseconds from Python.
  raw = raw.replace(/(\.\d{3})\d+/, '$1')

  const date = new Date(raw)
  return Number.isNaN(date.getTime()) ? null : date
}

/** `29 Sep 2026` (UTC) */
export function formatDate(value) {
  const date = toUtcDate(value)
  if (!date) return '—'
  return `${pad(date.getUTCDate())} ${MONTHS[date.getUTCMonth()]} ${date.getUTCFullYear()}`
}

/** `11:18` (UTC) */
export function formatTime(value) {
  const date = toUtcDate(value)
  if (!date) return '—'
  return `${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}`
}

/** `29 Sep 2026, 11:18` (UTC) */
export function formatDateTime(value) {
  const date = toUtcDate(value)
  if (!date) return '—'
  return `${formatDate(date)}, ${formatTime(date)}`
}

/** `2026-09-29` — for `datetime-local`/`date` inputs and compact tables. */
export function toDateInput(value) {
  const date = toUtcDate(value)
  if (!date) return ''
  return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())}`
}

export function isValidDate(value) {
  return toUtcDate(value) !== null
}
