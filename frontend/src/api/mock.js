// In-memory mock backend for the DFIP API. Used when VITE_USE_MOCK !== 'false'.
//
// NOTE: the accounts below are mock-only demo accounts. The password is a
// demo value for this in-browser fake and is not a real credential.
//
// Routes live in the `routes` table below. To add a new area (sales,
// forecasts, dashboard), push more entries onto that table.

import { reorderQty, classifyRisk } from '../lib/planning.js'

const LATENCY_MS = 250
const MOCK_PASSWORD = 'password123'
const ROLES = ['admin', 'planner', 'viewer']

let db = null

function pad2(n) {
  return String(n).padStart(2, '0')
}

function formatDate(d) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
}

function todayString() {
  return formatDate(new Date())
}

// Strict YYYY-MM-DD that is also a real calendar date.
function isValidDateString(s) {
  if (typeof s !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(s)) return false
  const [y, m, d] = s.split('-').map(Number)
  const dt = new Date(y, m - 1, d)
  return dt.getFullYear() === y && dt.getMonth() === m - 1 && dt.getDate() === d
}

// Deterministic 60 days of history ending yesterday (weekly cycle plus a slow seasonal drift).
function seedSales(products) {
  const sales = []
  let id = 1
  const days = 60
  for (const p of products) {
    for (let i = days; i >= 1; i--) {
      const d = new Date()
      d.setDate(d.getDate() - i)
      const weekly = Math.sin(((d.getDay() + p.id) / 7) * 2 * Math.PI)
      const seasonal = Math.cos((i / days) * Math.PI)
      const base = 8 + ((p.id * 5) % 9)
      const qty = Math.max(
        0,
        Math.round(base * (1 + 0.35 * weekly + 0.2 * seasonal) + ((i * p.id) % 3)),
      )
      sales.push({ id: id++, product_id: p.id, sale_date: formatDate(d), quantity_sold: qty })
    }
  }
  return sales
}

function seed() {
  const now = new Date().toISOString()
  const users = [
    { id: 1, name: 'Alice Admin', email: 'admin@dfip.local', role: 'admin' },
    { id: 2, name: 'Paul Planner', email: 'planner@dfip.local', role: 'planner' },
    { id: 3, name: 'Vera Viewer', email: 'viewer@dfip.local', role: 'viewer' },
  ].map((u) => ({ ...u, password: MOCK_PASSWORD, is_active: true, created_at: now }))

  const rows = [
    ['SKU-1001', 'Whole Milk 1L', 'Dairy', 'carton', 40, 3.0, 120],
    ['SKU-1002', 'Free-Range Eggs (12)', 'Dairy', 'box', 30, 2.5, 0],
    ['SKU-1003', 'Sourdough Loaf', 'Bakery', 'each', 20, 2.0, 15],
    ['SKU-1004', 'Basmati Rice 5kg', 'Pantry', 'bag', 25, 4.0, 90],
    ['SKU-1005', 'Olive Oil 750ml', 'Pantry', 'bottle', 15, 3.0, 4200],
    ['SKU-1006', 'Bananas (per kg)', 'Produce', 'kg', 50, 2.0, 60],
    ['SKU-1007', 'Laundry Detergent 2L', 'Household', 'bottle', 12, 3.5, 35],
    ['SKU-1008', 'Instant Coffee 200g', 'Beverages', 'jar', 18, 3.0, 22],
  ]
  const products = rows.map((r, i) => ({
    id: i + 1,
    sku: r[0],
    name: r[1],
    category: r[2],
    unit: r[3],
    safety_stock: r[4],
    overstock_factor: r[5],
    is_active: true,
    created_at: now,
  }))
  const inventory = rows.map((r, i) => ({
    product_id: i + 1,
    quantity: r[6],
    updated_at: now,
    updated_by: 'admin@dfip.local',
  }))
  const sales = seedSales(products)
  return {
    users,
    products,
    inventory,
    sales,
    nextUserId: 4,
    nextProductId: rows.length + 1,
    nextSaleId: sales.length + 1,
  }
}

export function resetMockDb() {
  db = seed()
}
resetMockDb()

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const reply = (status, data) => ({ status, data })
const forbidden = () => reply(403, { detail: 'Not enough permissions' })

function validationError(details) {
  return reply(422, { code: 'validation_error', message: 'Validation failed', details })
}

const publicUser = ({ password, ...rest }) => rest
const isInt = (v) => typeof v === 'number' && Number.isInteger(v)

function productOut(p) {
  const inv = db.inventory.find((i) => i.product_id === p.id)
  return { ...p, quantity: inv ? inv.quantity : 0 }
}

function inventoryOut(inv) {
  const p = db.products.find((x) => x.id === inv.product_id)
  return {
    product_id: inv.product_id,
    sku: p.sku,
    name: p.name,
    quantity: inv.quantity,
    updated_at: inv.updated_at,
    updated_by: inv.updated_by,
  }
}

function checkProductFields(body, { create }) {
  const errors = []
  const allowed = ['sku', 'name', 'category', 'unit', 'safety_stock', 'overstock_factor']
  if (create) allowed.push('initial_quantity')
  if (!body || typeof body !== 'object' || Array.isArray(body)) {
    return [{ field: 'body', message: 'Request body must be an object' }]
  }
  for (const key of Object.keys(body)) {
    if (!allowed.includes(key)) errors.push({ field: key, message: 'Unknown field' })
  }
  if (create || 'sku' in body) {
    const sku = body.sku
    if (typeof sku !== 'string' || sku.length < 1 || sku.length > 50) {
      errors.push({ field: 'sku', message: 'SKU must be 1-50 characters' })
    } else if (!/^[A-Za-z0-9_-]+$/.test(sku)) {
      errors.push({ field: 'sku', message: 'SKU may contain only letters, digits, - and _' })
    }
  }
  if (create || 'name' in body) {
    const n = body.name
    if (typeof n !== 'string' || n.trim().length < 1 || n.length > 200) {
      errors.push({ field: 'name', message: 'Name must be 1-200 characters' })
    }
  }
  for (const f of ['category', 'unit']) {
    if (f in body && body[f] !== null && typeof body[f] !== 'string') {
      errors.push({ field: f, message: `${f} must be a string` })
    }
  }
  if ('safety_stock' in body && !(isInt(body.safety_stock) && body.safety_stock >= 0)) {
    errors.push({ field: 'safety_stock', message: 'Safety stock must be an integer >= 0' })
  }
  if ('overstock_factor' in body) {
    const f = body.overstock_factor
    if (!(typeof f === 'number' && f > 0 && f <= 10)) {
      errors.push({ field: 'overstock_factor', message: 'Overstock factor must be > 0 and <= 10' })
    }
  }
  if (create && 'initial_quantity' in body) {
    if (!(isInt(body.initial_quantity) && body.initial_quantity >= 0)) {
      errors.push({ field: 'initial_quantity', message: 'Initial quantity must be an integer >= 0' })
    }
  }
  return errors
}

function skuTaken(sku, exceptId) {
  return db.products.some(
    (p) => p.id !== exceptId && p.sku.toLowerCase() === String(sku).toLowerCase(),
  )
}

const skuExists = () =>
  reply(409, { code: 'sku_exists', message: 'A product with this SKU already exists', details: [] })
const productNotFound = () =>
  reply(404, { code: 'product_not_found', message: 'Product not found', details: [] })
const userNotFound = () =>
  reply(404, { code: 'user_not_found', message: 'User not found', details: [] })

function findProduct(id) {
  return db.products.find((p) => p.id === Number(id))
}

function saleOut(s) {
  const p = db.products.find((x) => x.id === s.product_id)
  return {
    id: s.id,
    product_id: s.product_id,
    sku: p.sku,
    name: p.name,
    sale_date: s.sale_date,
    quantity_sold: s.quantity_sold,
  }
}

const saleExists = () =>
  reply(409, {
    code: 'sale_exists',
    message: 'A sales record already exists for this product and date',
    details: [],
  })

const invalidCsv = (message) => reply(422, { code: 'invalid_csv', message, details: [] })

const round1 = (n) => Math.round(n * 10) / 10

// Provisional dashboard payload: naive forecast = average daily sales of the last 28 days * 7.
function buildDashboard() {
  const HORIZON = 7
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const dayStr = (offset) => {
    const d = new Date(today)
    d.setDate(d.getDate() + offset)
    return formatDate(d)
  }
  const active = db.products.filter((p) => p.is_active)
  const activeIds = new Set(active.map((p) => p.id))
  const recentStart = dayStr(-28)
  const todayStr = dayStr(0)

  const items = active.map((p) => {
    const inv = db.inventory.find((i) => i.product_id === p.id)
    const currentStock = inv ? inv.quantity : 0
    const sold = db.sales
      .filter((s) => s.product_id === p.id && s.sale_date >= recentStart && s.sale_date < todayStr)
      .reduce((sum, s) => sum + s.quantity_sold, 0)
    const forecastDemand = round1((sold / 28) * HORIZON)
    return {
      product_id: p.id,
      sku: p.sku,
      name: p.name,
      current_stock: currentStock,
      forecast_demand: forecastDemand,
      safety_stock: p.safety_stock,
      overstock_factor: p.overstock_factor,
      reorder_qty: reorderQty(forecastDemand, p.safety_stock, currentStock),
      risk: classifyRisk(currentStock, forecastDemand, p.overstock_factor),
    }
  })

  const totalForecast = items.reduce((sum, i) => sum + i.forecast_demand, 0)
  const dailyForecast = round1(totalForecast / HORIZON)
  const actualByDate = new Map()
  for (const s of db.sales) {
    if (!activeIds.has(s.product_id)) continue
    actualByDate.set(s.sale_date, (actualByDate.get(s.sale_date) || 0) + s.quantity_sold)
  }

  const trend = []
  for (let off = -30; off <= -1; off++) {
    const date = dayStr(off)
    const actual = actualByDate.get(date) || 0
    trend.push({ date, actual, forecast: off === -1 ? actual : null })
  }
  for (let off = 0; off < HORIZON; off++) {
    trend.push({ date: dayStr(off), actual: null, forecast: dailyForecast })
  }

  return {
    generated_at: new Date().toISOString(),
    horizon_days: HORIZON,
    totals: {
      current_stock: items.reduce((sum, i) => sum + i.current_stock, 0),
      forecast_demand: round1(totalForecast),
      reorder_count: items.filter((i) => i.reorder_qty > 0).length,
      stockout_count: items.filter((i) => i.risk === 'stockout').length,
      overstock_count: items.filter((i) => i.risk === 'overstock').length,
      product_count: items.length,
    },
    items,
    trend,
  }
}

const WRITERS = ['admin', 'planner']
const ADMIN_ONLY = ['admin']

const routes = [
  // Auth
  {
    method: 'POST',
    path: '/api/auth/login',
    public: true,
    handler: ({ body }) => {
      const email = body && typeof body.email === 'string' ? body.email.trim().toLowerCase() : ''
      const user = db.users.find((u) => u.email.toLowerCase() === email)
      if (!user || !body || user.password !== body.password) {
        return reply(401, { detail: 'Invalid email or password' })
      }
      if (!user.is_active) return reply(403, { detail: 'Account is inactive' })
      return reply(200, {
        access_token: `mock-token-${user.id}`,
        token_type: 'bearer',
        role: user.role,
      })
    },
  },
  { method: 'POST', path: '/api/auth/logout', handler: () => reply(200, { detail: 'Logged out' }) },

  // Products
  {
    method: 'GET',
    path: '/api/products',
    handler: ({ query }) => {
      const include = String(query.include_inactive) === 'true'
      return reply(200, db.products.filter((p) => include || p.is_active).map(productOut))
    },
  },
  {
    method: 'POST',
    path: '/api/products',
    roles: ADMIN_ONLY,
    handler: ({ body }) => {
      const errors = checkProductFields(body, { create: true })
      if (errors.length) return validationError(errors)
      if (skuTaken(body.sku)) return skuExists()
      const product = {
        id: db.nextProductId++,
        sku: body.sku,
        name: body.name,
        category: body.category ?? null,
        unit: body.unit ?? null,
        safety_stock: body.safety_stock ?? 0,
        overstock_factor: body.overstock_factor ?? 3.0,
        is_active: true,
        created_at: new Date().toISOString(),
      }
      db.products.push(product)
      db.inventory.push({
        product_id: product.id,
        quantity: body.initial_quantity ?? 0,
        updated_at: product.created_at,
        updated_by: 'system',
      })
      return reply(201, productOut(product))
    },
  },
  {
    method: 'GET',
    path: '/api/products/:id',
    handler: ({ params }) => {
      const p = findProduct(params.id)
      return p ? reply(200, productOut(p)) : productNotFound()
    },
  },
  {
    method: 'PUT',
    path: '/api/products/:id',
    roles: ADMIN_ONLY,
    handler: ({ params, body }) => {
      const p = findProduct(params.id)
      if (!p) return productNotFound()
      const errors = checkProductFields(body, { create: false })
      if (errors.length) return validationError(errors)
      if ('sku' in body && skuTaken(body.sku, p.id)) return skuExists()
      Object.assign(p, body)
      return reply(200, productOut(p))
    },
  },
  {
    method: 'PATCH',
    path: '/api/products/:id/deactivate',
    roles: ADMIN_ONLY,
    handler: ({ params }) => {
      const p = findProduct(params.id)
      if (!p) return productNotFound()
      p.is_active = false
      return reply(200, productOut(p))
    },
  },

  // Inventory
  {
    method: 'GET',
    path: '/api/inventory',
    handler: () =>
      reply(
        200,
        db.inventory
          .filter((i) => db.products.find((p) => p.id === i.product_id).is_active)
          .map(inventoryOut),
      ),
  },
  {
    method: 'GET',
    path: '/api/inventory/:id',
    handler: ({ params }) => {
      const inv = db.inventory.find((i) => i.product_id === Number(params.id))
      return inv ? reply(200, inventoryOut(inv)) : productNotFound()
    },
  },
  {
    method: 'PUT',
    path: '/api/inventory/:id',
    roles: WRITERS,
    handler: ({ params, body, user }) => {
      const inv = db.inventory.find((i) => i.product_id === Number(params.id))
      if (!inv) return productNotFound()
      const errors = []
      if (!body || typeof body !== 'object' || Array.isArray(body)) {
        errors.push({ field: 'body', message: 'Request body must be an object' })
      } else {
        for (const key of Object.keys(body)) {
          if (key !== 'quantity') errors.push({ field: key, message: 'Unknown field' })
        }
        if (!isInt(body.quantity) || body.quantity < 0) {
          errors.push({ field: 'quantity', message: 'Quantity must be an integer >= 0' })
        }
      }
      if (errors.length) return validationError(errors)
      const p = db.products.find((x) => x.id === inv.product_id)
      if (!p.is_active) {
        return reply(409, { code: 'product_inactive', message: 'Product is inactive', details: [] })
      }
      inv.quantity = body.quantity
      inv.updated_at = new Date().toISOString()
      inv.updated_by = user.email
      return reply(200, inventoryOut(inv))
    },
  },

  // Sales (provisional contract, see README)
  {
    method: 'GET',
    path: '/api/sales',
    handler: ({ query }) => {
      const errors = []
      const { product_id: pid, start_date: start, end_date: end } = query
      const hasVal = (v) => v !== undefined && v !== null && v !== ''
      if (hasVal(pid) && !/^\d+$/.test(String(pid))) {
        errors.push({ field: 'product_id', message: 'Product id must be an integer' })
      }
      if (hasVal(start) && !isValidDateString(start)) {
        errors.push({ field: 'start_date', message: 'Start date must be YYYY-MM-DD' })
      }
      if (hasVal(end) && !isValidDateString(end)) {
        errors.push({ field: 'end_date', message: 'End date must be YYYY-MM-DD' })
      }
      if (!errors.length && hasVal(start) && hasVal(end) && start > end) {
        errors.push({ field: 'start_date', message: 'Start date must be on or before end date' })
      }
      if (errors.length) return validationError(errors)
      const rows = db.sales
        .filter(
          (s) =>
            (!hasVal(pid) || s.product_id === Number(pid)) &&
            (!hasVal(start) || s.sale_date >= start) &&
            (!hasVal(end) || s.sale_date <= end),
        )
        .sort((a, b) =>
          a.sale_date === b.sale_date ? b.id - a.id : a.sale_date < b.sale_date ? 1 : -1,
        )
      return reply(200, rows.map(saleOut))
    },
  },
  {
    method: 'POST',
    path: '/api/sales',
    roles: WRITERS,
    handler: ({ body }) => {
      if (!body || typeof body !== 'object' || Array.isArray(body)) {
        return validationError([{ field: 'body', message: 'Request body must be an object' }])
      }
      const errors = []
      for (const key of Object.keys(body)) {
        if (!['product_id', 'sale_date', 'quantity_sold'].includes(key)) {
          errors.push({ field: key, message: 'Unknown field' })
        }
      }
      if (!isInt(body.product_id)) {
        errors.push({ field: 'product_id', message: 'Product is required' })
      }
      if (!isValidDateString(body.sale_date)) {
        errors.push({ field: 'sale_date', message: 'Date must be a valid YYYY-MM-DD date' })
      } else if (body.sale_date > todayString()) {
        errors.push({ field: 'sale_date', message: 'Date cannot be in the future' })
      }
      if (!isInt(body.quantity_sold) || body.quantity_sold < 0) {
        errors.push({ field: 'quantity_sold', message: 'Quantity sold must be an integer >= 0' })
      }
      if (errors.length) return validationError(errors)
      const p = findProduct(body.product_id)
      if (!p) return productNotFound()
      if (db.sales.some((s) => s.product_id === p.id && s.sale_date === body.sale_date)) {
        return saleExists()
      }
      const sale = {
        id: db.nextSaleId++,
        product_id: p.id,
        sale_date: body.sale_date,
        quantity_sold: body.quantity_sold,
      }
      db.sales.push(sale)
      return reply(201, saleOut(sale))
    },
  },
  {
    method: 'POST',
    path: '/api/sales/import',
    roles: WRITERS,
    // The body is the CSV text (in mock mode the client reads the uploaded file).
    handler: ({ body }) => {
      const text = typeof body === 'string' ? body.replace(/^﻿/, '') : ''
      if (!text.trim()) return invalidCsv('The CSV file is empty')
      const lines = text.split(/\r?\n/)
      const header = lines[0].split(',').map((h) => h.trim().toLowerCase())
      if (header.join(',') !== 'sku,date,quantity_sold') {
        return invalidCsv('Header must be exactly: sku,date,quantity_sold')
      }
      const today = todayString()
      const seen = new Set()
      const accepted = []
      const rejected = []
      for (let i = 1; i < lines.length; i++) {
        if (!lines[i].trim()) continue
        const row = i + 1
        const cols = lines[i].split(',').map((c) => c.trim())
        if (cols.length !== 3) {
          rejected.push({ row, message: 'Expected 3 columns: sku,date,quantity_sold' })
          continue
        }
        const [sku, date, qty] = cols
        const product = db.products.find((p) => p.sku.toLowerCase() === sku.toLowerCase())
        if (!product) {
          rejected.push({ row, message: `Unknown SKU: ${sku}` })
        } else if (!isValidDateString(date)) {
          rejected.push({ row, message: 'Date must be in YYYY-MM-DD format' })
        } else if (date > today) {
          rejected.push({ row, message: 'Date cannot be in the future' })
        } else if (!/^-?\d+$/.test(qty)) {
          rejected.push({ row, message: 'Quantity sold must be a whole number' })
        } else if (Number(qty) < 0) {
          rejected.push({ row, message: 'Quantity sold cannot be negative' })
        } else if (seen.has(`${product.id}|${date}`)) {
          rejected.push({ row, message: 'Duplicate product and date in this file' })
        } else if (db.sales.some((s) => s.product_id === product.id && s.sale_date === date)) {
          rejected.push({
            row,
            message: 'A sales record already exists for this product and date',
          })
        } else {
          seen.add(`${product.id}|${date}`)
          accepted.push({ product_id: product.id, sale_date: date, quantity_sold: Number(qty) })
        }
      }
      for (const a of accepted) db.sales.push({ id: db.nextSaleId++, ...a })
      return reply(200, { imported: accepted.length, rejected })
    },
  },

  // Dashboard (provisional contract, see README)
  { method: 'GET', path: '/api/dashboard', handler: () => reply(200, buildDashboard()) },

  // Users (admin only)
  {
    method: 'GET',
    path: '/api/users',
    roles: ['admin'],
    handler: () => reply(200, db.users.map(publicUser)),
  },
  {
    method: 'POST',
    path: '/api/users',
    roles: ['admin'],
    handler: ({ body }) => {
      const errors = []
      const b = body && typeof body === 'object' ? body : {}
      for (const key of Object.keys(b)) {
        if (!['name', 'email', 'password', 'role'].includes(key)) {
          errors.push({ field: key, message: 'Unknown field' })
        }
      }
      if (typeof b.name !== 'string' || !b.name.trim()) {
        errors.push({ field: 'name', message: 'Name is required' })
      }
      if (typeof b.email !== 'string' || !/^[^@\s]+@[^@\s]+$/.test(b.email)) {
        errors.push({ field: 'email', message: 'Enter a valid email' })
      }
      if (typeof b.password !== 'string' || b.password.length < 8) {
        errors.push({ field: 'password', message: 'Password must be at least 8 characters' })
      }
      if (!ROLES.includes(b.role)) errors.push({ field: 'role', message: 'Invalid role' })
      if (errors.length) return validationError(errors)
      if (db.users.some((u) => u.email.toLowerCase() === b.email.toLowerCase())) {
        return reply(409, {
          code: 'email_exists',
          message: 'A user with this email already exists',
          details: [],
        })
      }
      const user = {
        id: db.nextUserId++,
        name: b.name,
        email: b.email,
        password: b.password,
        role: b.role,
        is_active: true,
        created_at: new Date().toISOString(),
      }
      db.users.push(user)
      return reply(201, publicUser(user))
    },
  },
  {
    method: 'PATCH',
    path: '/api/users/:id/role',
    roles: ['admin'],
    handler: ({ params, body }) => {
      const u = db.users.find((x) => x.id === Number(params.id))
      if (!u) return userNotFound()
      if (!body || !ROLES.includes(body.role)) {
        return validationError([{ field: 'role', message: 'Invalid role' }])
      }
      u.role = body.role
      return reply(200, publicUser(u))
    },
  },
  {
    method: 'PATCH',
    path: '/api/users/:id/deactivate',
    roles: ['admin'],
    handler: ({ params }) => {
      const u = db.users.find((x) => x.id === Number(params.id))
      if (!u) return userNotFound()
      u.is_active = false
      return reply(200, publicUser(u))
    },
  },
]

function compile(path) {
  const keys = []
  const source = path.replace(/:([a-z_]+)/g, (_, k) => {
    keys.push(k)
    return '([^/]+)'
  })
  return { re: new RegExp('^' + source + '$'), keys }
}
for (const r of routes) Object.assign(r, compile(r.path))

function userFromToken(token) {
  const m = /^mock-token-(\d+)$/.exec(token || '')
  if (!m) return null
  const u = db.users.find((x) => x.id === Number(m[1]))
  return u && u.is_active ? u : null
}

export async function mockRequest(method, path, { body, query, token } = {}) {
  await sleep(LATENCY_MS)
  const m = String(method).toUpperCase()
  const q = query || {}

  let pathMatched = false
  for (const route of routes) {
    const match = route.re.exec(path)
    if (!match) continue
    pathMatched = true
    if (route.method !== m) continue
    const params = {}
    route.keys.forEach((k, i) => {
      params[k] = match[i + 1]
    })
    let user = null
    if (!route.public) {
      user = userFromToken(token)
      if (!user) return reply(401, { detail: 'Not authenticated' })
      if (route.roles && !route.roles.includes(user.role)) return forbidden()
    }
    // Round-trip the body through JSON to mimic the wire format.
    const wireBody = body === undefined ? undefined : JSON.parse(JSON.stringify(body))
    return route.handler({ params, body: wireBody, query: q, user })
  }
  return pathMatched
    ? reply(405, { detail: 'Method Not Allowed' })
    : reply(404, { detail: 'Not Found' })
}
