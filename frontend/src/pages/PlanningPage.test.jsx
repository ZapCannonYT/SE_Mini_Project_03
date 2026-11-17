import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderPage, signIn } from '../test/helpers.jsx'
import { createForecast } from '../api/endpoints.js'
import PlanningPage, { validateOverrides } from './PlanningPage.jsx'

async function setup(role = 'planner') {
  // SKU-1002 has no stock, so its forecast always shows up as a stockout alert.
  await signIn('planner')
  await createForecast({ productId: 2, horizon: 2, unit: 'week' })
  await signIn(role)
  const user = userEvent.setup()
  renderPage(<PlanningPage />)
  if (role === 'viewer') await screen.findByText('SKU-1002')
  else await screen.findByRole('option', { name: /SKU-1002/ })
  return user
}

describe('PlanningPage', () => {
  it('shows reorder quantity, risk and the inputs used (TC-PLAN-04)', async () => {
    const user = await setup()
    await user.selectOptions(screen.getByLabelText('Product'), '2')
    await screen.findByRole('option', { name: /#1 - 2 weeks/ })
    await user.click(screen.getByRole('button', { name: 'Calculate' }))

    const result = await screen.findByTestId('recommendation')
    expect(within(screen.getByTestId('result-risk')).getByText('Stockout')).toBeInTheDocument()
    const reorder = Number(within(screen.getByTestId('result-reorder')).getByText(/^\d+$/).textContent)
    expect(reorder).toBeGreaterThan(0)
    for (const label of ['Current stock', 'Forecast demand', 'Safety stock', 'Overstock factor', 'Forecast']) {
      expect(within(result).getByText(label)).toBeInTheDocument()
    }
    expect(within(result).getByText('Current stock').closest('tr')).toHaveTextContent('0')
    expect(within(result).getByText('Safety stock').closest('tr')).toHaveTextContent('30')
  })

  it('uses override values and reports them back', async () => {
    const user = await setup()
    await user.selectOptions(screen.getByLabelText('Product'), '2')
    await screen.findByRole('option', { name: /#1 - 2 weeks/ })
    await user.type(screen.getByLabelText(/Current stock/), '5000')
    await user.type(screen.getByLabelText(/Safety stock/), '7')
    await user.type(screen.getByLabelText(/Overstock factor/), '2')
    await user.click(screen.getByRole('button', { name: 'Calculate' }))
    const result = await screen.findByTestId('recommendation')
    expect(within(result).getByText('Current stock').closest('tr')).toHaveTextContent('5000')
    expect(within(result).getByText('Safety stock').closest('tr')).toHaveTextContent('7')
    expect(within(screen.getByTestId('result-risk')).getByText('Overstock')).toBeInTheDocument()
    expect(within(screen.getByTestId('result-reorder')).getByText('0')).toBeInTheDocument()
  })

  it('lists products at risk from the alerts endpoint (TC-PLAN-04)', async () => {
    await setup()
    const row = (await screen.findByText('SKU-1002')).closest('tr')
    expect(within(row).getByText('Stockout')).toBeInTheDocument()
  })

  it('asks for a forecast first when the product has none', async () => {
    const user = await setup()
    await user.selectOptions(screen.getByLabelText('Product'), '3')
    expect(await screen.findByRole('option', { name: 'No forecasts' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Calculate' }))
    expect(screen.getByText('Generate a forecast for this product first')).toBeInTheDocument()
    expect(screen.queryByTestId('recommendation')).not.toBeInTheDocument()
  })

  it('hides the calculator from viewers but still shows alerts', async () => {
    await setup('viewer')
    expect(screen.queryByRole('button', { name: 'Calculate' })).not.toBeInTheDocument()
    expect(await screen.findByText('SKU-1002')).toBeInTheDocument()
  })

  it('validateOverrides rejects bad numbers', () => {
    const base = { current_stock: '', safety_stock: '', overstock_factor: '' }
    expect(validateOverrides({ ...base, current_stock: '-1' }, '2', '1').current_stock).toBe('Cannot be negative')
    expect(validateOverrides({ ...base, safety_stock: '1.5' }, '2', '1').safety_stock).toBe('Enter a whole number')
    expect(validateOverrides({ ...base, overstock_factor: '11' }, '2', '1').overstock_factor).toBe('Must be between 1 and 10')
    expect(validateOverrides(base, '2', '1')).toEqual({})
  })
})
