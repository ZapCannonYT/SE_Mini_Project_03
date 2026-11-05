// In-memory mock backend for the DFIP API. Used when VITE_USE_MOCK !== 'false'.
//
// NOTE: the accounts below are mock-only demo accounts. The password is a
// demo value for this in-browser fake and is not a real credential.
//
// Routes live in the `routes` table below. To add a new area (sales,
// forecasts, dashboard), push more entries onto that table.

const LATENCY_MS = 250
const MOCK_PASSWORD = 'password123'
const ROLES = ['admin', 'planner', 'viewer']

let db = null

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
  return { users, products, inventory, nextUserId: 4, nextProductId: rows.length + 1 }
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
