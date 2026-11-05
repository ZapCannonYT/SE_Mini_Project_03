import { useCallback, useEffect, useState } from 'react'
import { useAuth, hasRole } from '../auth/AuthContext.jsx'
import * as api from '../api/endpoints.js'
import FormField from '../components/FormField.jsx'

function todayString() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function validateSale(values) {
  const errors = {}
  if (!values.product_id) errors.product_id = 'Product is required'
  if (!values.sale_date) errors.sale_date = 'Date is required'
  else if (values.sale_date > todayString()) errors.sale_date = 'Date cannot be in the future'
  const q = values.quantity_sold.trim()
  if (!q) errors.quantity_sold = 'Quantity sold is required'
  else if (!Number.isFinite(Number(q))) errors.quantity_sold = 'Quantity sold must be a whole number'
  else if (Number(q) < 0) errors.quantity_sold = 'Quantity sold cannot be negative'
  else if (!Number.isInteger(Number(q))) errors.quantity_sold = 'Quantity sold must be a whole number'
  return errors
}

const EMPTY_FILTER = { product_id: '', start_date: '', end_date: '' }
const EMPTY_SALE = { product_id: '', sale_date: '', quantity_sold: '' }

export default function SalesPage() {
  const { user } = useAuth()
  const canWrite = hasRole(user, 'admin', 'planner')

  const [products, setProducts] = useState([])
  const [sales, setSales] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')

  const [filter, setFilter] = useState(EMPTY_FILTER)
  const [applied, setApplied] = useState(EMPTY_FILTER)
  const [filterErrors, setFilterErrors] = useState({})

  const [sale, setSale] = useState(EMPTY_SALE)
  const [saleErrors, setSaleErrors] = useState({})
  const [saleServerError, setSaleServerError] = useState('')
  const [saleSuccess, setSaleSuccess] = useState('')
  const [saleSubmitting, setSaleSubmitting] = useState(false)

  const [file, setFile] = useState(null)
  const [fileInputKey, setFileInputKey] = useState(0)
  const [fileError, setFileError] = useState('')
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState(null)

  const loadSales = useCallback(async (f) => {
    setLoadError('')
    try {
      setSales(
        await api.listSales({
          productId: f.product_id,
          startDate: f.start_date,
          endDate: f.end_date,
        }),
      )
    } catch (err) {
      setLoadError(err.message || 'Could not load sales')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSales(applied)
  }, [loadSales, applied])

  useEffect(() => {
    api
      .listProducts(false)
      .then(setProducts)
      .catch((err) => setLoadError(err.message || 'Could not load products'))
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

  async function onAddSale(e) {
    e.preventDefault()
    setSaleSuccess('')
    setSaleServerError('')
    const found = validateSale(sale)
    setSaleErrors(found)
    if (Object.keys(found).length) return
    setSaleSubmitting(true)
    try {
      await api.createSale({
        product_id: Number(sale.product_id),
        sale_date: sale.sale_date,
        quantity_sold: Number(sale.quantity_sold.trim()),
      })
      setSaleSuccess('Sale recorded')
      setSale(EMPTY_SALE)
      await loadSales(applied)
    } catch (err) {
      if (err.status === 422 && err.details?.length) {
        const mapped = {}
        const other = []
        for (const d of err.details) {
          if (d.field && d.field in EMPTY_SALE) mapped[d.field] = d.message
          else other.push(d.message)
        }
        setSaleErrors(mapped)
        if (other.length) setSaleServerError(other.join('; '))
      } else if (err.status === 409 && err.code === 'sale_exists') {
        setSaleServerError(err.message || 'A sales record already exists for this product and date')
      } else {
        setSaleServerError(err.message || 'Could not record the sale')
      }
    } finally {
      setSaleSubmitting(false)
    }
  }

  async function onImport(e) {
    e.preventDefault()
    setImportResult(null)
    if (!file) {
      setFileError('Choose a CSV file to upload')
      return
    }
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setFileError('File must be a .csv file')
      return
    }
    setFileError('')
    setImporting(true)
    try {
      const res = await api.importSalesCsv(file)
      setImportResult(res)
      setFile(null)
      setFileInputKey((k) => k + 1)
      await loadSales(applied)
    } catch (err) {
      setFileError(err.message || 'Could not import the file')
    } finally {
      setImporting(false)
    }
  }

  const productOptions = products.map((p) => (
    <option key={p.id} value={p.id}>
      {p.sku} - {p.name}
    </option>
  ))

  return (
    <section>
      <div className="page-header">
        <h1>Sales</h1>
      </div>

      <div role="alert">{loadError && <div className="alert alert-error">{loadError}</div>}</div>

      <div className="card section-card">
        <h2>Sales history</h2>
        <form className="form form-inline" onSubmit={onApply} noValidate>
          <FormField
            id="filter-product"
            as="select"
            label="Filter by product"
            value={filter.product_id}
            onChange={(e) => setFilter((f) => ({ ...f, product_id: e.target.value }))}
          >
            <option value="">All products</option>
            {productOptions}
          </FormField>
          <FormField
            id="filter-start"
            type="date"
            label="Start date"
            value={filter.start_date}
            onChange={(e) => setFilter((f) => ({ ...f, start_date: e.target.value }))}
            error={filterErrors.start_date}
          />
          <FormField
            id="filter-end"
            type="date"
            label="End date"
            value={filter.end_date}
            onChange={(e) => setFilter((f) => ({ ...f, end_date: e.target.value }))}
            error={filterErrors.end_date}
          />
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
          <p className="muted">Loading sales...</p>
        ) : (
          <>
            <p className="muted" role="status">
              {sales.length} {sales.length === 1 ? 'record' : 'records'}
            </p>
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>SKU</th>
                  <th>Product</th>
                  <th>Quantity sold</th>
                </tr>
              </thead>
              <tbody>
                {sales.length === 0 && (
                  <tr>
                    <td colSpan={4} className="muted">
                      No sales records found
                    </td>
                  </tr>
                )}
                {sales.map((s) => (
                  <tr key={s.id}>
                    <td>{s.sale_date}</td>
                    <td>{s.sku}</td>
                    <td>{s.name}</td>
                    <td>{s.quantity_sold}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>

      {canWrite && (
        <div className="card section-card">
          <h2>Add sale</h2>
          <div role="status">
            {saleSuccess && <div className="alert alert-success">{saleSuccess}</div>}
          </div>
          <div role="alert">
            {saleServerError && <div className="alert alert-error">{saleServerError}</div>}
          </div>
          <form className="form" onSubmit={onAddSale} noValidate>
            <FormField
              id="sale-product"
              as="select"
              label="Product"
              value={sale.product_id}
              onChange={(e) => setSale((s) => ({ ...s, product_id: e.target.value }))}
              error={saleErrors.product_id}
            >
              <option value="">Select a product</option>
              {productOptions}
            </FormField>
            <FormField
              id="sale-date"
              type="date"
              label="Date"
              value={sale.sale_date}
              onChange={(e) => setSale((s) => ({ ...s, sale_date: e.target.value }))}
              error={saleErrors.sale_date}
            />
            <FormField
              id="sale-quantity"
              label="Quantity sold"
              inputMode="numeric"
              value={sale.quantity_sold}
              onChange={(e) => setSale((s) => ({ ...s, quantity_sold: e.target.value }))}
              error={saleErrors.quantity_sold}
            />
            <div className="toolbar">
              <button type="submit" className="btn btn-primary" disabled={saleSubmitting}>
                {saleSubmitting ? 'Saving...' : 'Add sale'}
              </button>
            </div>
          </form>
        </div>
      )}

      {canWrite && (
        <div className="card section-card">
          <h2>Import sales from CSV</h2>
          <p className="muted">
            Required columns: <code>sku,date,quantity_sold</code>. Dates use YYYY-MM-DD. Example:
          </p>
          <pre className="csv-example">
            {'sku,date,quantity_sold\nSKU-1001,2026-01-15,12\nSKU-1002,2026-01-15,7'}
          </pre>
          <form className="form" onSubmit={onImport} noValidate>
            <FormField
              key={fileInputKey}
              id="sales-csv"
              type="file"
              accept=".csv"
              label="CSV file"
              onChange={(e) => {
                setFile(e.target.files?.[0] ?? null)
                setFileError('')
              }}
              error={fileError}
            />
            <div className="toolbar">
              <button type="submit" className="btn btn-primary" disabled={importing}>
                {importing ? 'Uploading...' : 'Upload'}
              </button>
            </div>
          </form>

          {importResult && (
            <div className="import-result" role="status">
              <div className="alert alert-success">{importResult.imported} rows imported</div>
              {importResult.rejected.length > 0 && (
                <>
                  <h3>Rejected rows ({importResult.rejected.length})</h3>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Row</th>
                        <th>Message</th>
                      </tr>
                    </thead>
                    <tbody>
                      {importResult.rejected.map((r) => (
                        <tr key={r.row}>
                          <td>{r.row}</td>
                          <td>{r.message}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
