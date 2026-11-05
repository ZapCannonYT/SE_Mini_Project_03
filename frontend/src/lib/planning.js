// Planning rules; must match backend/app/analytics/planning.py.

export function reorderQty(forecastDemand, safetyStock, currentStock) {
  return Math.max(0, Math.ceil(forecastDemand + safetyStock - currentStock))
}

// Exact thresholds are not a risk.
export function classifyRisk(currentStock, forecastDemand, overstockFactor) {
  if (currentStock < forecastDemand) return 'stockout'
  if (currentStock > overstockFactor * forecastDemand) return 'overstock'
  return 'none'
}
