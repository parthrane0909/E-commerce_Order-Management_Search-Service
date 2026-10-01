/** Shared, UI-independent validation for the product form. */

export const SKU_PATTERN = /^[A-Za-z0-9][A-Za-z0-9\-_]*$/

export function validateSku(value) {
  const sku = String(value ?? '').trim()
  if (!sku) return 'SKU is required.'
  if (sku.length < 2 || sku.length > 64) return 'SKU must be between 2 and 64 characters.'
  if (!SKU_PATTERN.test(sku)) {
    return 'SKU must start with a letter or number and use only letters, numbers, “-” or “_”.'
  }
  return ''
}

export function validateTitle(value) {
  const title = String(value ?? '').trim()
  if (!title) return 'Title is required.'
  if (title.length < 2 || title.length > 200) return 'Title must be between 2 and 200 characters.'
  return ''
}

export function validatePrice(value) {
  if (value === '' || value === null || value === undefined) return 'Price is required.'
  const price = Number(value)
  if (!Number.isFinite(price)) return 'Price must be a number.'
  if (price <= 0) return 'Price must be greater than 0.'
  if (price > 1_000_000) return 'Price must be 1,000,000 or less.'
  return ''
}

export function validateCategory(value) {
  const category = String(value ?? '').trim()
  if (!category) return 'Category is required.'
  if (category.length < 2 || category.length > 64) {
    return 'Category must be between 2 and 64 characters.'
  }
  return ''
}

/** Per-row variant validation — returns `{ sku?, stock? }` (empty = valid). */
export function validateVariant(row) {
  const errors = {}
  const sku = String(row?.sku ?? '').trim()
  if (!sku) errors.sku = 'SKU required'
  else if (sku.length > 64) errors.sku = 'Max 64 chars'

  const stockRaw = row?.stock
  if (stockRaw === '' || stockRaw === null || stockRaw === undefined) {
    errors.stock = 'Required'
  } else {
    const stock = Number(stockRaw)
    if (!Number.isFinite(stock) || !Number.isInteger(stock) || stock < 0) {
      errors.stock = '0 or more'
    } else if (stock > 100_000) {
      errors.stock = 'Max 100,000'
    }
  }
  return errors
}

export function validateVariants(rows) {
  return (rows || []).map((row) => validateVariant(row))
}

/** Duplicate/empty attribute keys → message, otherwise empty string. */
export function validateAttributeKeys(rows) {
  const seen = new Set()
  for (const row of rows || []) {
    const key = String(row.key ?? '').trim()
    if (!key) return 'Attribute keys cannot be empty.'
    if (seen.has(key)) return `Duplicate attribute key “${key}”.`
    seen.add(key)
  }
  return ''
}

/**
 * Coerce an attribute value typed in the editor:
 * `"5"` → 5, `"true"` → true, everything else stays a string.
 */
export function coerceAttributeValue(raw) {
  const value = String(raw ?? '').trim()
  if (value === '') return ''
  if (/^-?\d+(\.\d+)?$/.test(value)) return Number(value)
  if (value === 'true') return true
  if (value === 'false') return false
  return value
}
