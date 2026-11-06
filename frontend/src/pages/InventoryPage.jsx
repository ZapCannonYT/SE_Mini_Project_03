import { useCallback, useEffect, useState } from 'react'
import { useAuth, hasRole } from '../auth/AuthContext.jsx'
import * as api from '../api/endpoints.js'

export function validateQuantity(text) {
  const t = text.trim()
  if (!t) return 'Quantity is required'
  const n = Number(t)
  if (!Number.isFinite(n)) return 'Quantity must be a whole number'
  if (n < 0) return 'Quantity cannot be negative'
  if (!Number.isInteger(n)) return 'Quantity must be a whole number'
  return ''
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString()
}

export default function InventoryPage() {
  const { user } = useAuth()
  const canWrite = hasRole(user, 'admin', 'planner')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [drafts, setDrafts] = useState({})
  const [rowErrors, setRowErrors] = useState({})
  const [saving, setSaving] = useState({})
  const [saved, setSaved] = useState('')

  const load = useCallback(async () => {
    try {
      const list = await api.listInventory()
      setItems(list)
      setDrafts(Object.fromEntries(list.map((i) => [i.product_id, String(i.quantity)])))
    } catch (err) {
      setLoadError(err.message || 'Could not load inventory')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function onSave(item) {
    const id = item.product_id
    setSaved('')
    const message = validateQuantity(drafts[id] ?? '')
    if (message) {
      setRowErrors((e) => ({ ...e, [id]: message }))
      return
    }
    setRowErrors((e) => ({ ...e, [id]: '' }))
    setSaving((s) => ({ ...s, [id]: true }))
    try {
      const updated = await api.updateInventory(id, Number(drafts[id].trim()))
      setItems((list) => list.map((i) => (i.product_id === id ? updated : i)))
      setDrafts((d) => ({ ...d, [id]: String(updated.quantity) }))
      setSaved(`Quantity for ${item.sku} updated`)
    } catch (err) {
      const detail = err.details?.[0]?.message
      setRowErrors((e) => ({ ...e, [id]: detail || err.message || 'Could not update quantity' }))
    } finally {
      setSaving((s) => ({ ...s, [id]: false }))
    }
  }

  return (
    <section>
      <div className="page-header">
        <h1>Inventory</h1>
      </div>

      {!canWrite && <div className="card note">You have read-only access to inventory.</div>}
      <div role="status">{saved && <div className="alert alert-success">{saved}</div>}</div>
      <div role="alert">{loadError && <div className="alert alert-error">{loadError}</div>}</div>

      {loading ? (
        <p className="muted">Loading inventory...</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Name</th>
              <th>Quantity</th>
              <th>Last updated</th>
              {canWrite && <th>Update quantity</th>}
            </tr>
          </thead>
          <tbody>
            {items.length === 0 && (
              <tr>
                <td colSpan={canWrite ? 5 : 4} className="muted">
                  No inventory records found
                </td>
              </tr>
            )}
            {items.map((i) => {
              const id = i.product_id
              const error = rowErrors[id]
              return (
                <tr key={id}>
                  <td>{i.sku}</td>
                  <td>{i.name}</td>
                  <td>{i.quantity}</td>
                  <td>{formatTime(i.updated_at)}</td>
                  {canWrite && (
                    <td>
                      <div className="toolbar row-actions">
                        <input
                          type="text"
                          inputMode="numeric"
                          className="qty-input"
                          aria-label={`Quantity for ${i.sku}`}
                          aria-invalid={!!error}
                          aria-describedby={error ? `qty-error-${id}` : undefined}
                          value={drafts[id] ?? ''}
                          onChange={(e) => setDrafts((d) => ({ ...d, [id]: e.target.value }))}
                        />
                        <button
                          type="button"
                          className="btn btn-primary"
                          disabled={!!saving[id]}
                          onClick={() => onSave(i)}
                          aria-label={`Save ${i.sku}`}
                        >
                          {saving[id] ? 'Saving...' : 'Save'}
                        </button>
                      </div>
                      {error && (
                        <div id={`qty-error-${id}`} className="field-error">
                          {error}
                        </div>
                      )}
                    </td>
                  )}
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </section>
  )
}
