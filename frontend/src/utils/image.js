import { API_BASE_URL } from '../api/client'

const EXTERNAL = /^(?:[a-z][a-z0-9+.-]*:)?\/\//i
const DATA_LIKE = /^(?:data|blob):/i

/**
 * Turn a stored `image_url` into something the `<img>` tag can load.
 *
 * - Absolute URLs (`https://…`, `//cdn/…`) and `data:`/`blob:` values are
 *   returned untouched.
 * - Front-end assets shipped with the bundle (`/products/DESK-001.svg`) stay
 *   relative so they resolve against the app origin.
 * - Backend uploads (`/uploads/products/…`) are prefixed with the API origin
 *   when one is configured, so images still load when no dev/nginx proxy is
 *   in front of them.
 *
 * Returns `null` when there is nothing to render (the caller falls back to
 * the branded placeholder).
 */
export function resolveImageUrl(value) {
  const url = typeof value === 'string' ? value.trim() : ''
  if (!url) return null
  if (EXTERNAL.test(url) || DATA_LIKE.test(url)) return url
  if (url.startsWith('/uploads/') && API_BASE_URL) return `${API_BASE_URL}${url}`
  return url
}

export default resolveImageUrl
