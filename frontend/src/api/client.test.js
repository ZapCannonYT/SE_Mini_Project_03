import { request, ApiError } from './client.js'
import { setAuth } from '../auth/storage.js'
import { login } from './endpoints.js'

async function signIn(email) {
  const { access_token, role } = await login(email, 'password123')
  setAuth({ token: access_token, role, email })
}

describe('api client (mock mode)', () => {
  it('attaches the stored token so protected routes succeed', async () => {
    await signIn('admin@dfip.local')
    const products = await request('/api/products')
    expect(products.length).toBeGreaterThan(0)
  })

  it('throws ApiError with code and details on 422', async () => {
    await signIn('admin@dfip.local')
    const err = await request('/api/inventory/1', { method: 'PUT', body: { quantity: 1.5 } }).catch(
      (e) => e,
    )
    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(422)
    expect(err.code).toBe('validation_error')
    expect(err.details[0].field).toBe('quantity')
  })

  it('throws 401, clears auth and signals for a bad token', async () => {
    setAuth({ token: 'bogus', role: 'admin', email: 'x@y.z' })
    const handler = vi.fn()
    window.addEventListener('dfip:unauthorized', handler)
    const err = await request('/api/products').catch((e) => e)
    window.removeEventListener('dfip:unauthorized', handler)
    expect(err.status).toBe(401)
    expect(handler).toHaveBeenCalled()
    expect(localStorage.getItem('dfip.auth')).toBeNull()
  })

  it('enforces roles with 403', async () => {
    await signIn('viewer@dfip.local')
    const err = await request('/api/users').catch((e) => e)
    expect(err.status).toBe(403)
    expect(err.message).toBe('Not enough permissions')
  })

  it('rejects duplicate SKU case-insensitively with 409', async () => {
    await signIn('admin@dfip.local')
    const err = await request('/api/products', {
      method: 'POST',
      body: { sku: 'sku-1001', name: 'Dup' },
    }).catch((e) => e)
    expect(err.status).toBe(409)
    expect(err.code).toBe('sku_exists')
  })

  it('allows only admins to manage products, like the backend', async () => {
    await signIn('planner@dfip.local')
    const err = await request('/api/products', {
      method: 'POST',
      body: { sku: 'NEW-1', name: 'New' },
    }).catch((e) => e)
    expect(err.status).toBe(403)
  })
})
