import client from './client'

/** Seeded PostgreSQL users for the "Log In As" selector. */
export function listUsers() {
  return client.get('/api/users')
}
