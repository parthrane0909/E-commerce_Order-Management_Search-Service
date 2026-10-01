import { describe, it, expect } from 'vitest'
import { ORDER_STATUSES, isOrderStatus, statusLabel, statusTone, statusOptions } from '../src/utils/status'
import { formatDate, formatDateTime, formatTime, toUtcDate, toDateInput } from '../src/utils/dates'

describe('status helpers', () => {
  it('exposes exactly the three supported order statuses', () => {
    expect(ORDER_STATUSES).toEqual(['PENDING', 'PROCESSING', 'SHIPPED'])
    expect(statusOptions()).toEqual([
      { value: 'PENDING', label: 'Pending' },
      { value: 'PROCESSING', label: 'Processing' },
      { value: 'SHIPPED', label: 'Shipped' },
    ])
  })

  it('maps labels and design tones', () => {
    expect(statusLabel('PENDING')).toBe('Pending')
    expect(statusLabel('PROCESSING')).toBe('Processing')
    expect(statusLabel('SHIPPED')).toBe('Shipped')
    expect(statusLabel('')).toBe('Unknown')

    expect(statusTone('PENDING')).toBe('warning')
    expect(statusTone('PROCESSING')).toBe('info')
    expect(statusTone('SHIPPED')).toBe('success')
    expect(statusTone('OTHER')).toBe('neutral')
  })

  it('validates status values', () => {
    expect(isOrderStatus('PENDING')).toBe(true)
    expect(isOrderStatus('DELIVERED')).toBe(false)
    expect(isOrderStatus(undefined)).toBe(false)
  })
})

describe('date helpers', () => {
  it('renders naive API timestamps as UTC', () => {
    // MongoDB stores naive UTC strings — they must not shift with locale.
    expect(formatDate('2026-09-29T11:12:47.221000')).toBe('29 Sep 2026')
    expect(formatDateTime('2026-09-29T11:12:47.221000')).toBe('29 Sep 2026, 11:12')
    expect(formatTime('2026-09-29T11:12:47.221000')).toBe('11:12')
  })

  it('handles timezone-aware timestamps and month boundaries', () => {
    expect(formatDateTime('2026-01-01T23:30:00Z')).toBe('01 Jan 2026, 23:30')
    expect(formatDateTime('2026-12-31T00:05:00.123456Z')).toBe('31 Dec 2026, 00:05')
    expect(formatDate('2026-06-15T12:00:00+02:00')).toBe('15 Jun 2026')
  })

  it('supports date inputs and rejects junk', () => {
    expect(toDateInput('2026-09-29T11:12:47Z')).toBe('2026-09-29')
    expect(toUtcDate('')).toBeNull()
    expect(toUtcDate('not-a-date')).toBeNull()
    expect(formatDate(null)).toBe('—')
  })
})
