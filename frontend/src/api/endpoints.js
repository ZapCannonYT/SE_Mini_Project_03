import { request, isMockMode } from './client.js'

export const login = (email, password) =>
  request('/api/auth/login', { method: 'POST', body: { email, password } })
export const logout = () => request('/api/auth/logout', { method: 'POST' })

export const listProducts = (includeInactive) =>
  request('/api/products', { query: { include_inactive: includeInactive } })
export const getProduct = (id) => request(`/api/products/${id}`)
export const createProduct = (body) => request('/api/products', { method: 'POST', body })
export const updateProduct = (id, body) =>
  request(`/api/products/${id}`, { method: 'PUT', body })
export const deactivateProduct = (id) =>
  request(`/api/products/${id}/deactivate`, { method: 'PATCH' })

export const listInventory = () => request('/api/inventory')
export const getInventory = (productId) => request(`/api/inventory/${productId}`)
export const updateInventory = (productId, quantity) =>
  request(`/api/inventory/${productId}`, { method: 'PUT', body: { quantity } })

export const listUsers = () => request('/api/users')
export const createUser = (body) => request('/api/users', { method: 'POST', body })
export const changeUserRole = (id, role) =>
  request(`/api/users/${id}/role`, { method: 'PATCH', body: { role } })
export const deactivateUser = (id) =>
  request(`/api/users/${id}/deactivate`, { method: 'PATCH' })

// Sales endpoints are provisional until the backend story lands (see README).
export const listSales = ({ productId, startDate, endDate } = {}) =>
  request('/api/sales', {
    query: {
      product_id: productId || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    },
  })
export const createSale = (body) => request('/api/sales', { method: 'POST', body })
export async function importSalesCsv(file) {
  if (isMockMode()) {
    const text = await file.text()
    return request('/api/sales/import', { method: 'POST', body: text })
  }
  const formData = new FormData()
  formData.append('file', file)
  return request('/api/sales/import', { method: 'POST', body: formData, formData })
}
