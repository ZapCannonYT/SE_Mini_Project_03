import { setAuth } from '../auth/storage.js'
import { login, getDashboard } from './endpoints.js'
import { reorderQty, classifyRisk } from '../lib/planning.js'

async function signIn(role) {
  const email = `${role}@dfip.local`
  const { access_token } = await login(email, 'password123')
  setAuth({ token: access_token, role, email })
}

describe('mock /api/dashboard', () => {
  it('lets a viewer read it', async () => {
    await signIn('viewer')
    const d = await getDashboard()
    expect(d.horizon_days).toBe(7)
    expect(d.items).toHaveLength(8)
  })

  it('applies the planning rules to every item', async () => {
    await signIn('viewer')
    const d = await getDashboard()
    for (const i of d.items) {
      expect(i.reorder_qty).toBe(reorderQty(i.forecast_demand, i.safety_stock, i.current_stock))
      expect(i.risk).toBe(classifyRisk(i.current_stock, i.forecast_demand, i.overstock_factor))
    }
    const eggs = d.items.find((i) => i.sku === 'SKU-1002')
    expect(eggs.current_stock).toBe(0)
    expect(eggs.risk).toBe('stockout')
    expect(eggs.reorder_qty).toBe(Math.ceil(eggs.forecast_demand + 30))
    const oil = d.items.find((i) => i.sku === 'SKU-1005')
    expect(oil.risk).toBe('overstock')
    expect(oil.reorder_qty).toBe(0)
  })

  it('has totals consistent with the items and at least one of each risk', async () => {
    await signIn('viewer')
    const { totals, items } = await getDashboard()
    expect(totals.product_count).toBe(items.length)
    expect(totals.stockout_count).toBe(items.filter((i) => i.risk === 'stockout').length)
    expect(totals.overstock_count).toBe(items.filter((i) => i.risk === 'overstock').length)
    expect(totals.reorder_count).toBe(items.filter((i) => i.reorder_qty > 0).length)
    expect(totals.current_stock).toBe(items.reduce((s, i) => s + i.current_stock, 0))
    const f = items.reduce((s, i) => s + i.forecast_demand, 0)
    expect(totals.forecast_demand).toBeCloseTo(f, 1)
    expect(totals.stockout_count).toBeGreaterThan(0)
    expect(totals.overstock_count).toBeGreaterThan(0)
  })

  it('has 30 actual points then 7 forecast points', async () => {
    await signIn('viewer')
    const { trend } = await getDashboard()
    expect(trend).toHaveLength(37)
    expect(trend.slice(0, 30).every((t) => typeof t.actual === 'number')).toBe(true)
    expect(trend.slice(0, 29).every((t) => t.forecast === null)).toBe(true)
    expect(trend[29].forecast).toBe(trend[29].actual)
    expect(
      trend.slice(30).every((t) => t.actual === null && typeof t.forecast === 'number'),
    ).toBe(true)
  })

  it('requires authentication', async () => {
    await expect(getDashboard()).rejects.toMatchObject({ status: 401 })
  })
})
