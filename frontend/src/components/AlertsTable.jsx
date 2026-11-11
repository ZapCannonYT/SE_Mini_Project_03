import { useState } from 'react'

const FILTERS = [
  ['all', 'All'],
  ['stockout', 'Stockout'],
  ['overstock', 'Overstock'],
]

export function alertRows(items) {
  return items
    .filter((i) => i.risk === 'stockout' || i.risk === 'overstock')
    .sort((a, b) => {
      if (a.risk !== b.risk) return a.risk === 'stockout' ? -1 : 1
      return b.reorder_qty - a.reorder_qty
    })
}

export default function AlertsTable({ items }) {
  const [filter, setFilter] = useState('all')
  const all = alertRows(items)
  const rows = filter === 'all' ? all : all.filter((i) => i.risk === filter)

  return (
    <div>
      <div className="toolbar" role="group" aria-label="Filter alerts by risk type">
        {FILTERS.map(([value, label]) => (
          <button
            key={value}
            type="button"
            className={`btn ${filter === value ? 'btn-primary' : 'btn-secondary'}`}
            aria-pressed={filter === value}
            onClick={() => setFilter(value)}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="table-scroll">
        <table className="table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Product</th>
              <th>Current stock</th>
              <th>Forecast demand</th>
              <th>Reorder qty</th>
              <th>Risk</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td colSpan={6} className="muted">
                  No products are at risk.
                </td>
              </tr>
            )}
            {rows.map((i) => (
              <tr key={i.product_id}>
                <td>{i.sku}</td>
                <td>{i.name}</td>
                <td>{i.current_stock}</td>
                <td>{i.forecast_demand}</td>
                <td>{i.reorder_qty}</td>
                <td>
                  {i.risk === 'stockout' ? (
                    <span className="badge badge-stockout">Stockout</span>
                  ) : (
                    <span className="badge badge-overstock">Overstock</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
