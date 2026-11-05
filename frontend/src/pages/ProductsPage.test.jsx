import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderPage, signIn } from '../test/helpers.jsx'
import ProductsPage from './ProductsPage.jsx'

describe('ProductsPage', () => {
  it('lists products and hides write controls for planners', async () => {
    await signIn('planner')
    renderPage(<ProductsPage />)
    expect(await screen.findByText('SKU-1001')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'New product' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Edit/ })).not.toBeInTheDocument()
  })

  it('shows validation messages for empty name, SKU and negative safety stock', async () => {
    const user = userEvent.setup()
    await signIn('admin')
    renderPage(<ProductsPage />)
    await screen.findByText('SKU-1001')
    await user.click(screen.getByRole('button', { name: 'New product' }))
    await user.clear(screen.getByLabelText('Safety stock'))
    await user.type(screen.getByLabelText('Safety stock'), '-5')
    await user.click(screen.getByRole('button', { name: 'Create product' }))
    expect(screen.getByText('SKU is required')).toBeInTheDocument()
    expect(screen.getByText('Name is required')).toBeInTheDocument()
    expect(screen.getByText('Must be a whole number of 0 or more')).toBeInTheDocument()
  })

  it('creates a product as admin', async () => {
    const user = userEvent.setup()
    await signIn('admin')
    renderPage(<ProductsPage />)
    await screen.findByText('SKU-1001')
    await user.click(screen.getByRole('button', { name: 'New product' }))
    await user.type(screen.getByLabelText('SKU'), 'NEW-1')
    await user.type(screen.getByLabelText('Name'), 'Brand New Thing')
    await user.click(screen.getByRole('button', { name: 'Create product' }))
    expect(await screen.findByText('Product NEW-1 created')).toBeInTheDocument()
    expect(await screen.findByText('Brand New Thing')).toBeInTheDocument()
  })

  it('shows a SKU field error for a duplicate SKU', async () => {
    const user = userEvent.setup()
    await signIn('admin')
    renderPage(<ProductsPage />)
    await screen.findByText('SKU-1001')
    await user.click(screen.getByRole('button', { name: 'New product' }))
    await user.type(screen.getByLabelText('SKU'), 'SKU-1001')
    await user.type(screen.getByLabelText('Name'), 'Dup')
    await user.click(screen.getByRole('button', { name: 'Create product' }))
    expect(await screen.findByText('A product with this SKU already exists')).toBeInTheDocument()
  })
})
