import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderPage, signIn } from '../test/helpers.jsx'
import InventoryPage from './InventoryPage.jsx'

async function setupAs(role) {
  await signIn(role)
  renderPage(<InventoryPage />)
  await screen.findByText('SKU-1001')
}

describe('InventoryPage', () => {
  it('rejects negative and decimal quantities', async () => {
    const user = userEvent.setup()
    await setupAs('planner')
    const input = screen.getByLabelText('Quantity for SKU-1001')
    await user.clear(input)
    await user.type(input, '-3')
    await user.click(screen.getByRole('button', { name: 'Save SKU-1001' }))
    expect(screen.getByText('Quantity cannot be negative')).toBeInTheDocument()
    await user.clear(input)
    await user.type(input, '2.5')
    await user.click(screen.getByRole('button', { name: 'Save SKU-1001' }))
    expect(screen.getByText('Quantity must be a whole number')).toBeInTheDocument()
    await user.clear(input)
    await user.click(screen.getByRole('button', { name: 'Save SKU-1001' }))
    expect(screen.getByText('Quantity is required')).toBeInTheDocument()
  })

  it('saves a valid quantity', async () => {
    const user = userEvent.setup()
    await setupAs('admin')
    const input = screen.getByLabelText('Quantity for SKU-1001')
    await user.clear(input)
    await user.type(input, '77')
    await user.click(screen.getByRole('button', { name: 'Save SKU-1001' }))
    expect(await screen.findByText('Quantity for SKU-1001 updated')).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: '77' })).toBeInTheDocument()
  })

  it('is read-only for viewers', async () => {
    await setupAs('viewer')
    expect(screen.getByText(/read-only access/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Save/ })).not.toBeInTheDocument()
  })
})
