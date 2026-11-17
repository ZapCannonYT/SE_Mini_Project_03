import { useCallback, useEffect, useState } from 'react'
import * as api from '../api/endpoints.js'
import FormField from '../components/FormField.jsx'
import { formatDateTime, formatQty } from '../lib/format.js'

const EMPTY_FILTER = { product_id: '', start_date: '', end_date: '', risk: '' }

const RISK_LABEL = { none: 'OK', stockout: 'Stockout', overstock: 'Overstock' }
const RISK_CLASS = { none: 'badge-ok', stockout: 'badge-stockout', overstock: 'badge-overstock' }

const toFilters = (f) => ({
  productId: f.product_id,
  startDate: f.start_date,
  endDate: f.end_date,
  risk: f.risk,
})

function downloadText(text, filename) {
  const url = URL.createObjectURL(new Blob([text], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export default function ReportsPage() {
  const [products, setProducts] = useState([])
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [filter, setFilter] = useState(EMPTY_FILTER)
  const [applied, setApplied] = useState(EMPTY_FILTER)
  const [filterErrors, setFilterErrors] = useState({})
  const [exporting, setExporting] = useState(false)

  const load = useCallback(async (f) => {
    setLoading(true)
    setError('')
    try {
      setRows(await api.getPlanningReport(toFilters(f)))
    } catch (err) {
      setError(err.message || 'Could not load the report')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load(applied)
  }, [load, applied])

  useEffect(() => {
    api
      .listProducts(false)
      .then(setProducts)
      .catch((err) => setError(err.message || 'Could not load products'))
  }, [])

  function onApply(e) {
    e.preventDefault()
    const errors = {}
    if (filter.start_date && filter.end_date && filter.start_date > filter.end_date) {
      errors.start_date = 'Start date must be on or before end date'
    }
    setFilterErrors(errors)
    if (Object.keys(errors).length) return
    setApplied({ ...filter })
  }

  function onClear() {
    setFilter(EMPTY_FILTER)
    setFilterErrors({})
    setApplied(EMPTY_FILTER)
  }

  // The export uses the filters that produced the table, not unapplied edits in the form.
  async function onExport() {
    setExporting(true)
    setError('')
    try {
      downloadText(await api.exportPlanningReportCsv(toFilters(applied)), 'planning_report.csv')
    } catch (err) {
      setError(err.message || 'Could not export the report')
    } finally {
      setExporting(false)
    }
  }

  return (
    <section>
      <div className="page-header">
        <h1>Reports</h1>
        <button
          type="button"
          className="btn btn-primary"
          onClick={onExport}
          disabled={exporting || loading}
        >
          {exporting ? 'Exporting...' : 'Export CSV'}
        </button>
      </div>

      <div role="alert">{error && <div className="alert alert-error">{error}</div>}</div>

      <div className="card section-card">
        <h2>Planning report</h2>
        <p className="muted">
          Stored reorder recommendations with the inputs used for each. Filters apply to the table
          and to the CSV export.
        </p>
        <form className="form form-inline" onSubmit={onApply} noValidate>
          <FormField
            id="report-product"
            as="select"
            label="Product"
            value={filter.product_id}
            onChange={(e) => setFilter((f) => ({ ...f, product_id: e.target.value }))}
          >
            <option value="">All products</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.sku} - {p.name}
              </option>
            ))}
          </FormField>
          <FormField
            id="report-start"
            type="date"
            label="From date"
            value={filter.start_date}
            onChange={(e) => setFilter((f) => ({ ...f, start_date: e.target.value }))}
            error={filterErrors.start_date}
          />
          <FormField
            id="report-end"
            type="date"
            label="To date"
            value={filter.end_date}
            onChange={(e) => setFilter((f) => ({ ...f, end_date: e.target.value }))}
          />
          <FormField
            id="report-risk"
            as="select"
            label="Risk"
            value={filter.risk}
            onChange={(e) => setFilter((f) => ({ ...f, risk: e.target.value }))}
          >
            <option value="">All risks</option>
            <option value="stockout">Stockout</option>
            <option value="overstock">Overstock</option>
            <option value="none">OK</option>
          </FormField>
          <div className="toolbar">
            <button type="submit" className="btn btn-primary">
              Apply
            </button>
            <button type="button" className="btn btn-secondary" onClick={onClear}>
              Clear
            </button>
          </div>
        </form>

        {loading ? (
          <p className="muted">Loading report...</p>
        ) : (
          <>
            <p className="muted" role="status">
              {rows.length} {rows.length === 1 ? 'row' : 'rows'}
            </p>
            <div className="table-scroll">
              <table className="table">
                <thead>
                  <tr>
                    <th>Created</th>
                    <th>SKU</th>
                    <th>Product</th>
                    <th>Horizon</th>
                    <th>Current stock</th>
                    <th>Forecast demand</th>
                    <th>Safety stock</th>
                    <th>Overstock factor</th>
                    <th>Reorder qty</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.length === 0 && (
                    <tr>
                      <td colSpan={10} className="muted">
                        No recommendations match these filters.
                      </td>
                    </tr>
                  )}
                  {rows.map((r) => (
                    <tr key={r.recommendation_id}>
                      <td>{formatDateTime(r.created_at)}</td>
                      <td>{r.sku}</td>
                      <td>{r.name}</td>
                      <td>
                        {r.horizon} {r.unit}
                        {r.horizon === 1 ? '' : 's'}
                      </td>
                      <td>{r.current_stock}</td>
                      <td>{formatQty(r.forecast_demand)}</td>
                      <td>{r.safety_stock}</td>
                      <td>{r.overstock_factor}</td>
                      <td>{r.reorder_qty}</td>
                      <td>
                        <span className={`badge ${RISK_CLASS[r.risk]}`}>{RISK_LABEL[r.risk]}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </section>
  )
}
