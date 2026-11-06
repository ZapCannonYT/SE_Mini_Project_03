import { useState } from 'react'
import FormField from './FormField.jsx'

const WHOLE_NUMBER = /^\d+$/
const WHOLE_MESSAGE = 'Must be a whole number of 0 or more'

function initialValues(product) {
  if (!product) {
    return {
      sku: '',
      name: '',
      category: '',
      unit: 'unit',
      safety_stock: '0',
      overstock_factor: '1.5',
      initial_quantity: '0',
    }
  }
  return {
    sku: product.sku,
    name: product.name,
    category: product.category ?? '',
    unit: product.unit ?? '',
    safety_stock: String(product.safety_stock),
    overstock_factor: String(product.overstock_factor),
    initial_quantity: '0',
  }
}

export function validateProduct(values, { editing }) {
  const errors = {}
  if (!editing) {
    const sku = values.sku.trim()
    if (!sku) errors.sku = 'SKU is required'
    else if (sku.length > 50) errors.sku = 'SKU must be 50 characters or fewer'
    else if (!/^[A-Za-z0-9_-]+$/.test(sku)) {
      errors.sku = 'SKU may contain only letters, digits, - and _'
    }
  }
  if (!values.name.trim()) errors.name = 'Name is required'
  else if (values.name.trim().length > 200) errors.name = 'Name must be 200 characters or fewer'
  if (!WHOLE_NUMBER.test(values.safety_stock.trim())) errors.safety_stock = WHOLE_MESSAGE
  const factorText = values.overstock_factor.trim()
  const factor = Number(factorText)
  if (!factorText || !Number.isFinite(factor) || factor <= 0 || factor > 10) {
    errors.overstock_factor = 'Must be greater than 0 and at most 10'
  }
  if (!editing && !WHOLE_NUMBER.test(values.initial_quantity.trim())) {
    errors.initial_quantity = WHOLE_MESSAGE
  }
  return errors
}

function buildPayload(values, editing) {
  const payload = {
    name: values.name.trim(),
    category: values.category.trim() || null,
    unit: values.unit.trim() || 'unit',
    safety_stock: Number(values.safety_stock.trim()),
    overstock_factor: Number(values.overstock_factor.trim()),
  }
  if (!editing) {
    payload.sku = values.sku.trim()
    payload.initial_quantity = Number(values.initial_quantity.trim())
  }
  return payload
}

// `onSave(payload)` should return a promise and throw an ApiError on failure.
export default function ProductForm({ product, onSave, onCancel }) {
  const editing = !!product
  const [values, setValues] = useState(() => initialValues(product))
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const set = (field) => (e) => setValues((v) => ({ ...v, [field]: e.target.value }))

  async function onSubmit(e) {
    e.preventDefault()
    setServerError('')
    const found = validateProduct(values, { editing })
    setErrors(found)
    if (Object.keys(found).length) return
    setSubmitting(true)
    try {
      await onSave(buildPayload(values, editing))
    } catch (err) {
      if (err.status === 422 && err.details?.length) {
        const mapped = {}
        const other = []
        for (const d of err.details) {
          if (d.field && d.field in values) mapped[d.field] = d.message
          else other.push(d.message)
        }
        setErrors(mapped)
        if (other.length) setServerError(other.join('; '))
      } else if (err.status === 409 && err.code === 'sku_exists') {
        setErrors({ sku: err.message || 'A product with this SKU already exists' })
      } else {
        setServerError(err.message || 'Could not save the product')
      }
      setSubmitting(false)
    }
  }

  return (
    <div className="card form-card">
      <h2>{editing ? `Edit product ${product.sku}` : 'New product'}</h2>
      <div role="alert">{serverError && <div className="alert alert-error">{serverError}</div>}</div>
      <form className="form" onSubmit={onSubmit} noValidate>
        <FormField
          id="product-sku"
          label="SKU"
          value={values.sku}
          onChange={set('sku')}
          error={errors.sku}
          readOnly={editing}
        />
        <FormField
          id="product-name"
          label="Name"
          value={values.name}
          onChange={set('name')}
          error={errors.name}
        />
        <FormField
          id="product-category"
          label="Category"
          value={values.category}
          onChange={set('category')}
          error={errors.category}
        />
        <FormField
          id="product-unit"
          label="Unit"
          value={values.unit}
          onChange={set('unit')}
          error={errors.unit}
        />
        <FormField
          id="product-safety-stock"
          label="Safety stock"
          inputMode="numeric"
          value={values.safety_stock}
          onChange={set('safety_stock')}
          error={errors.safety_stock}
        />
        <FormField
          id="product-overstock-factor"
          label="Overstock factor"
          inputMode="decimal"
          value={values.overstock_factor}
          onChange={set('overstock_factor')}
          error={errors.overstock_factor}
        />
        {!editing && (
          <FormField
            id="product-initial-quantity"
            label="Initial quantity"
            inputMode="numeric"
            value={values.initial_quantity}
            onChange={set('initial_quantity')}
            error={errors.initial_quantity}
          />
        )}
        <div className="toolbar">
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Saving...' : editing ? 'Save changes' : 'Create product'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
