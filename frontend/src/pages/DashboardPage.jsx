import { useCallback, useEffect, useState } from 'react'
import * as api from '../api/endpoints.js'
import { isMockMode } from '../api/client.js'
import TrendChart from '../components/TrendChart.jsx'
import AlertsTable from '../components/AlertsTable.jsx'

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleTimeString()
}

function SummaryCard({ label, value, detail, accent, testId }) {
  return (
    <div className={`card summary-card${accent ? ` accent-${accent}` : ''}`} data-testid={testId}>
      <div className="summary-label">{label}</div>
      <div className="summary-value">{value}</div>
      <div className="muted summary-detail">{detail}</div>
    </div>
  )
}

export default function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setData(await api.getDashboard())
    } catch (err) {
      setError(err.message || 'Could not load the dashboard')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const t = data?.totals

  return (
    <section>
      <div className="page-header">
        <h1>Dashboard</h1>
        <div className="toolbar" style={{ marginBottom: 0 }}>
          {data && <span className="muted">Last updated {formatTime(data.generated_at)}</span>}
          <button type="button" className="btn btn-secondary" disabled={loading} onClick={load}>
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div role="alert" className="alert alert-error">
          {error}{' '}
          <button type="button" className="btn btn-secondary" onClick={load}>
            Retry
          </button>
        </div>
      )}

      {loading && !data && <p className="muted">Loading dashboard...</p>}

      {data && (
        <>
          <div className="grid-cards section-card">
            <SummaryCard
              testId="card-current-stock"
              label="Current stock"
              value={t.current_stock}
              detail={`units across ${t.product_count} products`}
            />
            <SummaryCard
              testId="card-forecast-demand"
              label="Forecast demand"
              value={t.forecast_demand}
              detail={`units, next ${data.horizon_days} days`}
            />
            <SummaryCard
              testId="card-reorder"
              label="Reorder recommended"
              value={t.reorder_count}
              detail="products"
            />
            <SummaryCard
              testId="card-stockout"
              label="Stockout risk"
              value={t.stockout_count}
              detail="products"
              accent="red"
            />
            <SummaryCard
              testId="card-overstock"
              label="Overstock risk"
              value={t.overstock_count}
              detail="products"
              accent="amber"
            />
          </div>

          <div className="card section-card">
            <h2>Sales trend and forecast</h2>
            <TrendChart trend={data.trend} />
          </div>

          <div className="card section-card">
            <h2>Alerts</h2>
            <AlertsTable items={data.items} />
            {isMockMode() && (
              <p className="muted">
                Values come from mock data until the forecasting API is connected.
              </p>
            )}
          </div>
        </>
      )}
    </section>
  )
}
