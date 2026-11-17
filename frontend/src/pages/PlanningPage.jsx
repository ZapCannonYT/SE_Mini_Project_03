import { useCallback, useEffect, useState } from 'react'
import { useAuth, hasRole } from '../auth/AuthContext.jsx'
import * as api from '../api/endpoints.js'
import FormField from '../components/FormField.jsx'
import AlertsTable from '../components/AlertsTable.jsx'
import { formatDateTime as formatTimestamp, formatQty } from '../lib/format.js'

const EMPTY_OVERRIDES = { current_stock: '', safety_stock: '', overstock_factor: '' }

export function validateOverrides(values, productId, forecastId) {
  const errors = {}
  if (!productId) errors.product_id = 'Product is required'
  else if (!forecastId) errors.forecast_id = 'Generate a forecast for this product first'
  for (const field of ['current_stock', 'safety_stock']) {
    const v = values[field].trim()
    if (!v) continue
    if (!/^-?\d+$/.test(v)) errors[field] = 'Enter a whole number'
    else if (Number(v) < 0) errors[field] = 'Cannot be negative'
  }
  const f = values.overstock_factor.trim()
  if (f) {
    if (!Number.isFinite(Number(f))) errors.overstock_factor = 'Enter a number'
    else if (Number(f) < 1 || Number(f) > 10) errors.overstock_factor = 'Must be between 1 and 10'
  }
  return errors
}

function RiskBadge({ risk }) {
  if (risk === 'stockout') return <span className="badge badge-stockout">Stockout</span>
  if (risk === 'overstock') return <span className="badge badge-overstock">Overstock</span>
  return <span className="badge badge-ok">No risk</span>
}

export default function PlanningPage() {
  const { user } = useAuth()
  const canPlan = hasRole(user, 'admin', 'planner')

  const [products, setProducts] = useState([])
  const [productId, setProductId] = useState('')
  const [forecasts, setForecasts] = useState([])
  const [forecastId, setForecastId] = useState('')
  const [overrides, setOverrides] = useState(EMPTY_OVERRIDES)
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [calculating, setCalculating] = useState(false)
  const [result, setResult] = useState(null)

  const [alerts, setAlerts] = useState([])
  const [alertsLoading, setAlertsLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  const loadAlerts = useCallback(async () => {
    try {
      setAlerts(await api.listPlanningAlerts())
    } catch (err) {
      setLoadError(err.message || 'Could not load alerts')
    } finally {
      setAlertsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadAlerts()
    api
      .listProducts(false)
      .then(setProducts)
      .catch((err) => setLoadError(err.message || 'Could not load products'))
  }, [loadAlerts])

  useEffect(() => {
    setResult(null)
    setForecastId('')
    if (!productId) {
      setForecasts([])
      return
    }
    api
      .listForecasts(productId)
      .then((list) => {
        setForecasts(list)
        setForecastId(list.length ? String(list[0].id) : '')
      })
      .catch((err) => setLoadError(err.message || 'Could not load forecasts'))
  }, [productId])

  async function onCalculate(e) {
    e.preventDefault()
    setServerError('')
    const found = validateOverrides(overrides, productId, forecastId)
    setErrors(found)
    if (Object.keys(found).length) return
    const body = { forecast_id: Number(forecastId) }
    if (overrides.current_stock.trim()) body.current_stock = Number(overrides.current_stock)
    if (overrides.safety_stock.trim()) body.safety_stock = Number(overrides.safety_stock)
    if (overrides.overstock_factor.trim()) body.overstock_factor = Number(overrides.overstock_factor)
    setCalculating(true)
    try {
      setResult(await api.createRecommendation(body))
      await loadAlerts()
    } catch (err) {
      setServerError(err.message || 'Could not calculate the recommendation')
    } finally {
      setCalculating(false)
    }
  }

  const usedForecast = result && forecasts.find((f) => f.id === result.forecast_id)
  const product = result && products.find((p) => p.id === result.product_id)

  return (
    <section>
      <div className="page-header">
        <h1>Planning</h1>
      </div>

      <div role="alert">{loadError && <div className="alert alert-error">{loadError}</div>}</div>

      {canPlan && (
        <div className="card section-card">
          <h2>Calculate a reorder recommendation</h2>
          <p className="muted">
            Uses the stored forecast for the product and its current stock. Leave the override
            fields empty to use the saved defaults.
          </p>
          <div role="alert">
            {serverError && <div className="alert alert-error">{serverError}</div>}
          </div>
          <form className="form form-inline" onSubmit={onCalculate} noValidate>
            <FormField
              id="plan-product"
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
              id="plan-forecast"
              as="select"
              label="Forecast"
              value={forecastId}
              onChange={(e) => setForecastId(e.target.value)}
              error={errors.forecast_id}
              disabled={!forecasts.length}
            >
              {forecasts.length === 0 && <option value="">No forecasts</option>}
              {forecasts.map((f) => (
                <option key={f.id} value={f.id}>
                  {`#${f.id} - ${f.horizon} ${f.unit}${f.horizon === 1 ? '' : 's'} - ${formatTimestamp(f.generated_at)}`}
                </option>
              ))}
            </FormField>
            <FormField
              id="plan-current-stock"
              label="Current stock (optional)"
              inputMode="numeric"
              value={overrides.current_stock}
              onChange={(e) => setOverrides((o) => ({ ...o, current_stock: e.target.value }))}
              error={errors.current_stock}
            />
            <FormField
              id="plan-safety-stock"
              label="Safety stock (optional)"
              inputMode="numeric"
              value={overrides.safety_stock}
              onChange={(e) => setOverrides((o) => ({ ...o, safety_stock: e.target.value }))}
              error={errors.safety_stock}
            />
            <FormField
              id="plan-overstock-factor"
              label="Overstock factor (optional)"
              inputMode="decimal"
              value={overrides.overstock_factor}
              onChange={(e) => setOverrides((o) => ({ ...o, overstock_factor: e.target.value }))}
              error={errors.overstock_factor}
            />
            <div className="toolbar">
              <button type="submit" className="btn btn-primary" disabled={calculating}>
                {calculating ? 'Calculating...' : 'Calculate'}
              </button>
            </div>
          </form>

          {result && (
            <div data-testid="recommendation" role="status">
              <h3>
                {product ? `${product.sku} - ${product.name}` : `Product ${result.product_id}`}
              </h3>
              <div className="grid-cards section-card">
                <div className="card summary-card" data-testid="result-reorder">
                  <div className="summary-label">Reorder quantity</div>
                  <div className="summary-value">{result.reorder_qty}</div>
                  <div className="muted summary-detail">units</div>
                </div>
                <div
                  className={`card summary-card${
                    result.risk === 'stockout'
                      ? ' accent-red'
                      : result.risk === 'overstock'
                        ? ' accent-amber'
                        : ''
                  }`}
                  data-testid="result-risk"
                >
                  <div className="summary-label">Risk</div>
                  <div className="summary-value">
                    <RiskBadge risk={result.risk} />
                  </div>
                  <div className="muted summary-detail">stockout or overstock</div>
                </div>
              </div>
              <h3>Inputs used</h3>
              <table className="table">
                <tbody>
                  <tr>
                    <th scope="row">Current stock</th>
                    <td>{result.current_stock}</td>
                  </tr>
                  <tr>
                    <th scope="row">Forecast demand</th>
                    <td>{formatQty(result.forecast_demand)}</td>
                  </tr>
                  <tr>
                    <th scope="row">Safety stock</th>
                    <td>{result.safety_stock}</td>
                  </tr>
                  <tr>
                    <th scope="row">Overstock factor</th>
                    <td>{result.overstock_factor}</td>
                  </tr>
                  <tr>
                    <th scope="row">Forecast</th>
                    <td>
                      #{result.forecast_id}
                      {usedForecast ? `, generated ${formatTimestamp(usedForecast.generated_at)}` : ''}
                    </td>
                  </tr>
                  <tr>
                    <th scope="row">Calculated</th>
                    <td>{formatTimestamp(result.created_at)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <div className="card section-card">
        <h2>Products at risk</h2>
        <p className="muted">
          From each product&apos;s latest forecast and current stock. Products without a forecast
          are not listed.
        </p>
        {alertsLoading ? <p className="muted">Loading alerts...</p> : <AlertsTable items={alerts} />}
      </div>
    </section>
  )
}
