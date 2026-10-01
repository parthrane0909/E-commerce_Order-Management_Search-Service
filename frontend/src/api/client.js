import axios from 'axios'

/**
 * Base URL for the FastAPI backend.
 * `VITE_API_BASE_URL || 'http://localhost:8000'` — setting it to an empty
 * string makes the app use relative /api requests (vite/nginx proxy).
 */
function resolveBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL
  if (configured === '') return ''
  return (configured || 'http://localhost:8000').replace(/\/+$/, '')
}

/** Error surfaced by the API layer — always carries a human readable message. */
export class ApiError extends Error {
  constructor(message, { code = 'unknown_error', status = 0, details = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
    this.details = details
  }
}

const client = axios.create({
  baseURL: resolveBaseUrl(),
  timeout: 20000,
  // FastAPI expects repeated keys for list params: ?tags=a&tags=b
  paramsSerializer: { indexes: null },
})

// Request interceptor to add Authorization header
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('meridian.auth.token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/** Convert any axios failure into an ApiError with a useful `.message`. */
export function toApiError(error) {
  if (error instanceof ApiError) return error

  const response = error?.response
  if (response) {
    const envelope = response.data?.error
    if (envelope && typeof envelope.message === 'string') {
      return new ApiError(envelope.message, {
        code: envelope.code || 'request_failed',
        status: response.status,
        details: envelope.details ?? null,
      })
    }
    if (typeof response.data === 'string' && response.data.trim()) {
      return new ApiError(response.data.trim(), {
        code: 'request_failed',
        status: response.status,
      })
    }
    return new ApiError(`The server returned an unexpected ${response.status} response.`, {
      code: 'request_failed',
      status: response.status,
    })
  }

  if (error?.request) {
    return new ApiError('Cannot reach the API server. Please check that the backend is running.', {
      code: 'network_error',
    })
  }

  return new ApiError(error?.message || 'Something went wrong.', { code: 'client_error' })
}

client.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(toApiError(error)),
)

/**
 * Map `details.fields` (FastAPI validation errors) or `details.field`
 * (app-level errors) to `{ fieldName: message }` for inline form errors.
 */
export function fieldErrorsFrom(error) {
  const details = error?.details
  if (!details || typeof details !== 'object') return {}

  const fields = Array.isArray(details.fields) ? details.fields : null
  if (fields) {
    return fields.reduce((acc, entry) => {
      const raw = String(entry?.field ?? '')
      const name = raw.replace(/^(body|query|path|params)\./, '')
      if (name && entry?.message) acc[name] = entry.message
      return acc
    }, {})
  }

  if (typeof details.field === 'string' && error?.message) {
    return { [details.field]: error.message }
  }

  return {}
}

/**
 * Best human-readable message for an ApiError: prefers explicit message,
 * falls back to joined `details.fields` messages (FastAPI 422 payloads).
 */
export function messageFrom(error) {
  if (!error) return 'Something went wrong.'
  const fields = error.details?.fields
  if (Array.isArray(fields) && fields.length) {
    const joined = fields
      .map((entry) => entry?.message)
      .filter(Boolean)
      .join(' ')
    if (joined) return joined
  }
  return error.message || 'Something went wrong.'
}

export default client
