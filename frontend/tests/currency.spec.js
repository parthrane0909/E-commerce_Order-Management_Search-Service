import { describe, it, expect } from 'vitest'
import { formatCurrency, formatNumber, parseAmount } from '../src/utils/currency'

describe('currency formatting', () => {
  it('formats money with two decimals and thousands separators', () => {
    expect(formatCurrency(0)).toBe('$0.00')
    expect(formatCurrency(384)).toBe('$384.00')
    expect(formatCurrency(7932.28)).toBe('$7,932.28')
    expect(formatCurrency(1234567.89)).toBe('$1,234,567.89')
  })

  it('accepts numeric strings from the API', () => {
    expect(formatCurrency('27.5')).toBe('$27.50')
  })

  it('returns an em dash for unusable values', () => {
    expect(formatCurrency(null)).toBe('—')
    expect(formatCurrency(undefined)).toBe('—')
    expect(formatCurrency('not-a-number')).toBe('—')
    expect(formatCurrency(Number.NaN)).toBe('—')
  })

  it('formats plain counts', () => {
    expect(formatNumber(47)).toBe('47')
    expect(formatNumber(7932)).toBe('7,932')
    expect(formatNumber('x')).toBe('—')
  })

  it('parses amounts defensively', () => {
    expect(parseAmount('19.99')).toBe(19.99)
    expect(parseAmount('')).toBeNull()
    expect(parseAmount('abc')).toBeNull()
    expect(parseAmount(null)).toBeNull()
  })
})
