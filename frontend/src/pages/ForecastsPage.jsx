import { useCallback, useEffect, useState } from 'react'
import { useAuth, hasRole } from '../auth/AuthContext.jsx'
import * as api from '../api/endpoints.js'
import FormField from '../components/FormField.jsx'
import ForecastChart from '../components/ForecastChart.jsx'

// Weekly horizons are 1-12 periods and monthly horizons 1-6 (API reference).
export const MAX_HORIZON = { week: 12, month: 6 }

export function formatTimestamp(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString()
}

export function validateForecast({ product_id, unit, horizon }) {
  const errors = {}
  if (!product_id) errors.product_id = 'Product is required'
  if (!MAX_HORIZON[unit]) errors.unit = 'Choose weeks or months'
  const n = Number(horizon)
  if (!String(horizon).trim()) errors.horizon = 'Horizon is required'
  else if (!Number.isInteger(n) || n < 1) errors.horizon = 'Horizon must be a whole number of 1 or more'
  else if (MAX_HORIZON[unit] && n > MAX_HORIZON[unit]) {
    errors.horizon = `Horizon can be at most ${MAX_HORIZON[unit]} ${unit}s`
  }
  return errors
}

export default function ForecastsPage() {
  const { user } = useAuth()
  const canGenerate = hasRole(user, 'admin', 'planner')

  const [products, setProducts] = useState([])
  const [productId, setProductId] = useState('')
  const [unit, setUnit] = useState('week')
  const [horizon, setHorizon] = useState('4')
  const [errors, setErrors] = useState({})

  const [forecasts, setForecasts] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [loadError, setLoadError] = useState('')
  const [serverError, setServerError] = useState('')

  useEffect(() => {
    api
      .listProducts(false)
      .then(setProducts)
      .catch((err) => setLoadError(err.message || 'Could not load products'))
  }, [])

  const loadForecasts = useCallback(async (id) => {
    setLoadError('')
    if (!id) {
      setForecasts([])
      setSelectedId(null)
      return
    }
    setLoading(true)
    try {
      const list = await api.listForecasts(id)
      setForecasts(list)
      setSelectedId(list.length ? list[0].id : null)
    } catch (err) {
      setLoadError(err.message || 'Could not load forecasts')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadForecasts(productId)
  }, [productId, loadForecasts])

  function onUnitChange(next) {
    setUnit(next)
    if (Number(horizon) > MAX_HORIZON[next]) setHorizon(String(MAX_HORIZON[next]))
  }

  async function onGenerate(e) {
    e.preventDefault()
    setServerError('')
    const found = validateForecast({ product_id: productId, unit, horizon })
    setErrors(found)
    if (Object.keys(found).length) return
    setGenerating(true)
    try {
      const created = await api.createForecast({
        productId: Number(productId),
        horizon: Number(horizon),
        unit,
      })
      setForecasts((list) => [created, ...list])
      setSelectedId(created.id)
    } catch (err) {
      setServerError(err.message || 'Could not generate the forecast')
    } finally {
      setGenerating(false)
    }
  }

  const selected = forecasts.find((f) => f.id === selectedId)
  const product = products.find((p) => String(p.id) === String(productId))

  return (
    <section>
      <div className="page-header">
        <h1>Forecasts</h1>
      </div>

      <div role="alert">{loadError && <div className="alert alert-error">{loadError}</div>}</div>

      <div className="card section-card">
        <h2>Generate a forecast</h2>
        {!canGenerate && (
          <p className="muted">Your role can view stored forecasts but not generate new ones.</p>
        )}
        <div role="alert">
          {serverError && <div className="alert alert-error">{serverError}</div>}
        </div>
        <form className="form form-inline" onSubmit={onGenerate} noValidate>
          <FormField
            id="forecast-product"
            as="select"
            label="Product"
            value={productId}
            onChange={(e) => {
              setProductId(e.target.value)
              setServerError('')
            }}
            error={errors.product_id}
          >
            <option value="">Select a product</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.sku} - {p.name}
              </option>
            ))}
          </FormField>
          <FormField
            id="forecast-unit"
            as="select"
            label="Period"
            value={unit}
            onChange={(e) => onUnitChange(e.target.value)}
            error={errors.unit}
          >
            <option value="week">Weekly</option>
            <option value="month">Monthly</option>
          </FormField>
          <FormField
            id="forecast-horizon"
            label={`Horizon (${unit}s, 1-${MAX_HORIZON[unit]})`}
            inputMode="numeric"
            value={horizon}
            onChange={(e) => setHorizon(e.target.value)}
            error={errors.horizon}
          />
          {canGenerate && (
            <div className="toolbar">
              <button type="submit" className="btn btn-primary" disabled={generating}>
                {generating ? 'Generating...' : 'Generate forecast'}
              </button>
            </div>
          )}
        </form>
      </div>

      {productId && loading && <p className="muted">Loading forecasts...</p>}

      {productId && !loading && !selected && (
        <div className="card section-card">
          <p className="muted">No forecast has been generated for this product yet.</p>
        </div>
      )}

      {selected && (
        <div className="card section-card" data-testid="forecast-result">
          <h2>
            {product ? `${product.sku} - ${product.name}` : `Product ${selected.product_id}`}
          </h2>
          <p className="muted">
            Horizon: {selected.horizon} {selected.unit}
            {selected.horizon === 1 ? '' : 's'} | Model: {selected.model_name} v
            {selected.model_version} | Generated: {formatTimestamp(selected.generated_at)}
          </p>
          <ForecastChart points={selected.points} unit={selected.unit} />
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>{selected.unit === 'week' ? 'Week' : 'Month'} starting</th>
                  <th>Forecast units</th>
                </tr>
              </thead>
              <tbody>
                {selected.points.map((p) => (
                  <tr key={p.period_start}>
                    <td>{p.period_start}</td>
                    <td>{p.predicted_qty}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {forecasts.length > 1 && (
        <div className="card section-card">
          <h2>Stored forecasts for this product</h2>
          <div className="table-scroll">
            <table className="table">
              <thead>
                <tr>
                  <th>Generated</th>
                  <th>Horizon</th>
                  <th>Model</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {forecasts.map((f) => (
                  <tr key={f.id}>
                    <td>{formatTimestamp(f.generated_at)}</td>
                    <td>
                      {f.horizon} {f.unit}
                      {f.horizon === 1 ? '' : 's'}
                    </td>
                    <td>{f.model_name}</td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-secondary"
                        aria-pressed={f.id === selectedId}
                        onClick={() => setSelectedId(f.id)}
                      >
                        {f.id === selectedId ? 'Shown' : 'Show'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  )
}
