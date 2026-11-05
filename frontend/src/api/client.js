import { getToken, clearAuth } from '../auth/storage.js'
import { mockRequest } from './mock.js'

export class ApiError extends Error {
  constructor(message, { status = 0, code = null, details = [] } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

export function isMockMode() {
  return import.meta.env.VITE_USE_MOCK !== 'false'
}

function buildQuery(query) {
  if (!query) return ''
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined && value !== null) params.append(key, String(value))
  }
  const s = params.toString()
  return s ? `?${s}` : ''
}

export async function request(path, { method = 'GET', body, query, formData } = {}) {
  const token = getToken()
  let status
  let data

  if (isMockMode()) {
    const res = await mockRequest(method, path, { body, query, token })
    status = res.status
    data = res.data
  } else {
    const base = import.meta.env.VITE_API_BASE_URL || ''
    const headers = { Accept: 'application/json' }
    // For FormData the browser sets the multipart Content-Type (with boundary).
    if (body !== undefined && !formData) headers['Content-Type'] = 'application/json'
    if (token) headers.Authorization = `Bearer ${token}`
    let res
    try {
      res = await fetch(`${base}${path}${buildQuery(query)}`, {
        method,
        headers,
        body: formData ? formData : body !== undefined ? JSON.stringify(body) : undefined,
      })
    } catch {
      throw new ApiError('Network error. Is the backend running?', { status: 0 })
    }
    status = res.status
    const text = await res.text()
    try {
      data = text ? JSON.parse(text) : null
    } catch {
      data = null
    }
  }

  if (status >= 200 && status < 300) return data

  if (status === 401 && path !== '/api/auth/login') {
    clearAuth()
    window.dispatchEvent(new Event('dfip:unauthorized'))
  }
  const obj = data && typeof data === 'object' ? data : {}
  const message =
    obj.message ||
    (typeof obj.detail === 'string' ? obj.detail : null) ||
    `Request failed (${status})`
  throw new ApiError(message, {
    status,
    code: obj.code || null,
    details: obj.details || [],
  })
}
