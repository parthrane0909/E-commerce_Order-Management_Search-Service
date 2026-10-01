import client from './client'

/**
 * Elasticsearch order search + aggregations.
 *
 * @param {{
 *   query?: string,
 *   status?: string[],
 *   date_from?: string,
 *   date_to?: string,
 *   min_price?: number,
 *   max_price?: number,
 *   page?: number,
 *   limit?: number,
 * }} payload
 */
export function searchOrders(payload = {}) {
  return client.post('/api/search/orders', payload)
}
