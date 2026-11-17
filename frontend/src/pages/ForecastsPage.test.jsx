import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { renderPage, signIn } from '../test/helpers.jsx'
import ForecastsPage, { validateForecast } from './ForecastsPage.jsx'

vi.mock('react-chartjs-2', () => ({
  Line: ({ data }) => (
    <div data-testid="forecast-chart">
      {data.datasets.map((d) => (
        <span key={d.label}>{d.label}</span>
      ))}
      <span data-testid="chart-points">{data.datasets[0].data.length}</span>
    </div>
  ),
}))

async function setup(role = 'planner') {
  await signIn(role)
  const user = userEvent.setup()
  renderPage(<ForecastsPage />)
  await screen.findByRole('option', { name: /SKU-1001/ })
  return user
}

describe('ForecastsPage', () => {
  it('generates a weekly forecast with chart, horizon and timestamp (TC-FCST-01, TC-FCST-02)', async () => {
    const user = await setup()
    await user.selectOptions(screen.getByLabelText('Product'), '1')
    await user.clear(screen.getByLabelText(/Horizon/))
    await user.type(screen.getByLabelText(/Horizon/), '6')
    await user.click(screen.getByRole('button', { name: 'Generate forecast' }))

    const result = await screen.findByTestId('forecast-result')
    expect(within(result).getByText(/SKU-1001 - Whole Milk 1L/)).toBeInTheDocument()
    expect(within(result).getByText(/Horizon: 6 weeks/)).toBeInTheDocument()
    expect(within(result).getByText(/Generated:/)).toBeInTheDocument()
    expect(within(result).getByTestId('chart-points')).toHaveTextContent('6')
    expect(within(result).getAllByRole('row')).toHaveLength(7) // header + 6 weeks
  })

  it('shows the insufficient-history message from the API (TC-FCST-01)', async () => {
    const user = await setup()
    await user.selectOptions(screen.getByLabelText('Product'), '1')
    await user.selectOptions(screen.getByLabelText('Period'), 'month')
    await user.click(screen.getByRole('button', { name: 'Generate forecast' }))
    expect(await screen.findByText(/At least 8 monthly periods/)).toBeInTheDocument()
    expect(screen.queryByTestId('forecast-result')).not.toBeInTheDocument()
  })

  it('validates the form before calling the API', async () => {
    const user = await setup()
    await user.click(screen.getByRole('button', { name: 'Generate forecast' }))
    expect(screen.getByText('Product is required')).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Product'), '1')
    await user.clear(screen.getByLabelText(/Horizon/))
    await user.type(screen.getByLabelText(/Horizon/), '13')
    await user.click(screen.getByRole('button', { name: 'Generate forecast' }))
    expect(screen.getByText('Horizon can be at most 12 weeks')).toBeInTheDocument()
    expect(screen.queryByTestId('forecast-result')).not.toBeInTheDocument()
  })

  it('shows stored forecasts when a product is selected again', async () => {
    const user = await setup()
    await user.selectOptions(screen.getByLabelText('Product'), '2')
    await user.click(screen.getByRole('button', { name: 'Generate forecast' }))
    await screen.findByTestId('forecast-result')
    await user.selectOptions(screen.getByLabelText('Product'), '3')
    expect(await screen.findByText(/No forecast has been generated/)).toBeInTheDocument()
    await user.selectOptions(screen.getByLabelText('Product'), '2')
    expect(await screen.findByTestId('forecast-result')).toBeInTheDocument()
  })

  it('lets a viewer see forecasts but not generate them', async () => {
    await setup('viewer')
    expect(screen.queryByRole('button', { name: 'Generate forecast' })).not.toBeInTheDocument()
    expect(screen.getByText(/can view stored forecasts/)).toBeInTheDocument()
  })

  it('validateForecast covers unit limits', () => {
    expect(validateForecast({ product_id: '1', unit: 'month', horizon: '7' }).horizon).toMatch(/at most 6/)
    expect(validateForecast({ product_id: '1', unit: 'week', horizon: '2.5' }).horizon).toMatch(/whole number/)
    expect(validateForecast({ product_id: '1', unit: 'week', horizon: '12' })).toEqual({})
  })
})
