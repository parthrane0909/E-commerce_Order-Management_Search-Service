import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // The app defaults to VITE_API_BASE_URL (absolute), but the proxy keeps
      // relative /api requests working when VITE_API_BASE_URL="" is set.
      // Inside Docker the API is reached as http://backend:8000 — override
      // with VITE_PROXY_TARGET (docker-compose sets it).
      '/api': {
        target: process.env.VITE_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    // Match the dev-server origin so the backend's CORS allowlist accepts
    // requests made from tests (tests talk to the live API, never mocks).
    environmentOptions: {
      jsdom: { url: 'http://localhost:5173/' },
    },
    include: ['tests/**/*.spec.js'],
    globals: false,
  },
})
