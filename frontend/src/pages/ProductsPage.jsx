import { useCallback, useEffect, useState } from 'react'
import { useAuth, hasRole } from '../auth/AuthContext.jsx'
import * as api from '../api/endpoints.js'
import ProductForm from '../components/ProductForm.jsx'

export default function ProductsPage() {
  const { user } = useAuth()
  const isAdmin = hasRole(user, 'admin')
  const [products, setProducts] = useState([])
  const [includeInactive, setIncludeInactive] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [actionError, setActionError] = useState('')
  const [success, setSuccess] = useState('')
  const [formMode, setFormMode] = useState(null) // null | 'create' | the product being edited

  const load = useCallback(async () => {
    setLoadError('')
    try {
      setProducts(await api.listProducts(includeInactive))
    } catch (err) {
      setLoadError(err.message || 'Could not load products')
    } finally {
      setLoading(false)
    }
  }, [includeInactive])

  useEffect(() => {
    load()
  }, [load])

  async function onSave(payload) {
    if (formMode === 'create') {
      const created = await api.createProduct(payload)
      setSuccess(`Product ${created.sku} created`)
    } else {
      const updated = await api.updateProduct(formMode.id, payload)
      setSuccess(`Product ${updated.sku} updated`)
    }
    setActionError('')
    setFormMode(null)
    await load()
  }

  async function onDeactivate(p) {
    setSuccess('')
    setActionError('')
    if (!window.confirm(`Deactivate product ${p.sku}?`)) return
    try {
      await api.deactivateProduct(p.id)
      setSuccess(`Product ${p.sku} deactivated`)
      await load()
    } catch (err) {
      setActionError(err.message || 'Could not deactivate the product')
    }
  }

  function openForm(mode) {
    setSuccess('')
    setActionError('')
    setFormMode(mode)
  }

  return (
    <section>
      <div className="page-header">
        <h1>Products</h1>
        {isAdmin && !formMode && (
          <button type="button" className="btn btn-primary" onClick={() => openForm('create')}>
            New product
          </button>
        )}
      </div>

      <div role="status">{success && <div className="alert alert-success">{success}</div>}</div>
      <div role="alert">
        {(loadError || actionError) && (
          <div className="alert alert-error">{loadError || actionError}</div>
        )}
      </div>

      {isAdmin && formMode && (
        <ProductForm
          key={formMode === 'create' ? 'create' : formMode.id}
          product={formMode === 'create' ? null : formMode}
          onSave={onSave}
          onCancel={() => setFormMode(null)}
        />
      )}

      <div className="toolbar">
        <label>
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
          />{' '}
          Show inactive
        </label>
      </div>

      {loading ? (
        <p className="muted">Loading products...</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Name</th>
              <th>Category</th>
              <th>Unit</th>
              <th>Safety stock</th>
              <th>Overstock factor</th>
              <th>Stock</th>
              <th>Status</th>
              {isAdmin && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {products.length === 0 && (
              <tr>
                <td colSpan={isAdmin ? 9 : 8} className="muted">
                  No products found
                </td>
              </tr>
            )}
            {products.map((p) => (
              <tr key={p.id}>
                <td>{p.sku}</td>
                <td>{p.name}</td>
                <td>{p.category ?? ''}</td>
                <td>{p.unit ?? ''}</td>
                <td>{p.safety_stock}</td>
                <td>{p.overstock_factor}</td>
                <td>{p.quantity}</td>
                <td>
                  <span className={p.is_active ? 'badge badge-ok' : 'badge'}>
                    {p.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                {isAdmin && (
                  <td>
                    <div className="toolbar row-actions">
                      <button
                        type="button"
                        className="btn btn-secondary"
                        onClick={() => openForm(p)}
                        aria-label={`Edit ${p.sku}`}
                      >
                        Edit
                      </button>
                      {p.is_active && (
                        <button
                          type="button"
                          className="btn btn-danger"
                          onClick={() => onDeactivate(p)}
                          aria-label={`Deactivate ${p.sku}`}
                        >
                          Deactivate
                        </button>
                      )}
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
