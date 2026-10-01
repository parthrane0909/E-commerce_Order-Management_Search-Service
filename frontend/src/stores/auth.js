import { defineStore } from 'pinia'
import client from '../api/client'
import router from '../router'

const TOKEN_KEY = 'meridian.auth.token'
const USER_KEY = 'meridian.auth.user'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || null,
    user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
    loading: false,
    error: '',
  }),

  getters: {
    isAuthenticated: (state) => !!state.token && !!state.user,
    isAdmin: (state) => state.user?.role === 'ADMIN',
    userName: (state) => state.user?.name || '',
    userEmail: (state) => state.user?.email || '',
    userId: (state) => state.user?.id || null,
  },

  actions: {
    async login(email, password) {
      this.loading = true
      this.error = ''
      try {
        const response = await client.post('/api/auth/login', { email, password })
        this.token = response.access_token
        this.user = response.user
        localStorage.setItem(TOKEN_KEY, this.token)
        localStorage.setItem(USER_KEY, JSON.stringify(this.user))
        // Redirect to intended page or storefront
        const redirect = router.currentRoute.value.query.redirect || '/'
        await router.push(redirect)
      } catch (err) {
        this.error = err?.message || 'Login failed'
        throw err
      } finally {
        this.loading = false
      }
    },

    async logout() {
      this.loading = true
      try {
        await client.post('/api/auth/logout')
      } catch {
        // Ignore logout errors
      } finally {
        this.token = null
        this.user = null
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
        this.loading = false
        await router.push({ name: 'login' })
      }
    },

    async fetchMe() {
      if (!this.token) return
      this.loading = true
      try {
        const response = await client.get('/api/auth/me')
        this.user = response
        localStorage.setItem(USER_KEY, JSON.stringify(this.user))
      } catch (err) {
        // Token invalid or expired
        this.token = null
        this.user = null
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
      } finally {
        this.loading = false
      }
    },

    async init() {
      if (this.token && this.user) {
        // Validate token by fetching current user
        await this.fetchMe()
      }
    },
  },
})