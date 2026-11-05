import { request, ApiError } from './client.js'
import { setAuth } from '../auth/storage.js'
import { login, createSale, listSales } from './endpoints.js'

async function signIn(role) {
  const email = `${role}@dfip.local`
  const { access_token } = await login(email, 'password123')
  setAuth({ token: access_token, role, email })
}

const importCsv = (text) => request('/api/sales/import', { method: 'POST', body: text })

describe('mock sales routes', () => {
  it('seeds 60 days of history ending yesterday', async () => {
    await signIn('viewer')
    const sales = await listSales({ productId: 1 })
    expect(sales).toHaveLength(60)
    const d = new Date()
    d.setDate(d.getDate() - 1)
    const pad = (n) => String(n).padStart(2, '0')
    expect(sales[0].sale_date).toBe(
      `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`,
    )
    expect(sales[0].sku).toBe('SKU-1001')
  })

  it('filters by date range and product, sorted by date desc', async () => {
    await signIn('viewer')
    const all = await listSales({ productId: 1 })
    const start = all[9].sale_date
    const end = all[4].sale_date
    const rows = await listSales({ productId: 1, startDate: start, endDate: end })
    expect(rows).toHaveLength(6)
    expect(rows[0].sale_date).toBe(end)
    expect(rows[5].sale_date).toBe(start)
  })

  it('rejects an inverted range with 422', async () => {
    await signIn('viewer')
    const err = await listSales({ startDate: '2026-02-10', endDate: '2026-02-01' }).catch((e) => e)
    expect(err.status).toBe(422)
  })

  it('creates a sale and returns 409 sale_exists for a duplicate', async () => {
    await signIn('planner')
    const body = { product_id: 1, sale_date: '2020-05-05', quantity_sold: 3 }
    const created = await createSale(body)
    expect(created.sku).toBe('SKU-1001')
    const err = await createSale(body).catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err.status).toBe(409)
    expect(err.code).toBe('sale_exists')
  })

  it('validates sale input and unknown product', async () => {
    await signIn('admin')
    const bad = await createSale({
      product_id: 1,
      sale_date: '2020-13-40',
      quantity_sold: -1,
    }).catch((e) => e)
    expect(bad.status).toBe(422)
    expect(bad.details.map((d) => d.field).sort()).toEqual(['quantity_sold', 'sale_date'])
    const future = await createSale({
      product_id: 1,
      sale_date: '2999-01-01',
      quantity_sold: 1,
    }).catch((e) => e)
    expect(future.details[0].message).toBe('Date cannot be in the future')
    const missing = await createSale({
      product_id: 999,
      sale_date: '2020-01-01',
      quantity_sold: 1,
    }).catch((e) => e)
    expect(missing.status).toBe(404)
  })

  it('forbids viewers from writing sales', async () => {
    await signIn('viewer')
    const err = await createSale({
      product_id: 1,
      sale_date: '2020-01-01',
      quantity_sold: 1,
    }).catch((e) => e)
    expect(err.status).toBe(403)
    const err2 = await importCsv('sku,date,quantity_sold').catch((e) => e)
    expect(err2.status).toBe(403)
  })

  it('imports valid rows and reports rejected ones with line numbers', async () => {
    await signIn('admin')
    const csv = [
      ' SKU,Date,Quantity_Sold ',
      'SKU-1001,2020-01-01,5',
      'SKU-1001,2020-01-01,6',
      'SKU-1002,2020-01-02,-1',
      'SKU-1002,2020-01-02,1.5',
      'SKU-1002,01/02/2020,1',
      'SKU-1002,2999-01-01,1',
      'SKU-9999,2020-01-02,1',
      'SKU-1003,2020-01-03',
      'SKU-1003,2020-01-03,4',
    ].join('\r\n')
    const res = await importCsv(csv)
    expect(res.imported).toBe(2)
    expect(res.rejected.map((r) => r.row)).toEqual([3, 4, 5, 6, 7, 8, 9])
    expect(res.rejected[0].message).toMatch(/Duplicate/)
    const stored = await listSales({ productId: 1, startDate: '2020-01-01', endDate: '2020-01-01' })
    expect(stored).toHaveLength(1)
    const again = await importCsv('sku,date,quantity_sold\nSKU-1001,2020-01-01,9')
    expect(again.imported).toBe(0)
    expect(again.rejected[0].message).toMatch(/already exists/)
  })

  it('rejects a wrong header or empty file and stores nothing', async () => {
    await signIn('admin')
    const before = (await listSales()).length
    const e1 = await importCsv('sku,date\nSKU-1001,2020-01-01').catch((e) => e)
    expect(e1.status).toBe(422)
    expect(e1.code).toBe('invalid_csv')
    const e2 = await importCsv('').catch((e) => e)
    expect(e2.code).toBe('invalid_csv')
    expect((await listSales()).length).toBe(before)
  })
})
