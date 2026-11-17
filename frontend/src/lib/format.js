// Display helpers shared by the forecast, planning and report screens.

// The API returns timestamps without a timezone designator (they are UTC). Treat them as UTC so
// the browser shows the user's local time instead of reading them as local already.
export function parseApiDate(iso) {
  if (!iso) return null
  const hasZone = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(iso)
  const d = new Date(hasZone ? iso : `${iso}Z`)
  return Number.isNaN(d.getTime()) ? null : d
}

export function formatDateTime(iso) {
  const d = parseApiDate(iso)
  return d ? d.toLocaleString() : (iso ?? '')
}

// Quantities such as forecast demand are floats; show at most 2 decimals (no 478.91999999999996).
export function formatQty(n) {
  const v = Number(n)
  return Number.isFinite(v) ? String(Number(v.toFixed(2))) : String(n ?? '')
}
