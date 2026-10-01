import client from './client'

/** Paginated catalog listing (MongoDB). */
export function listProducts(params = {}) {
  return client.get('/api/products', { params })
}

/** Facet counts for categories + tags (MongoDB). */
export function getProductFacets() {
  return client.get('/api/products/facets')
}

export function getProduct(id) {
  return client.get(`/api/products/${id}`)
}

export function createProduct(payload) {
  return client.post('/api/products', payload)
}

export function updateProduct(id, payload) {
  return client.patch(`/api/products/${id}`, payload)
}

/** Soft delete — the product is returned with `active: false`. */
export function deleteProduct(id) {
  return client.delete(`/api/products/${id}`)
}
