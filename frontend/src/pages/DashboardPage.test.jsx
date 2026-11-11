import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { renderPage, signIn } from '../test/helpers.jsx'
import { getDashboard } from '../api/endpoints.js'
import DashboardPage from './DashboardPage.jsx'

vi.mock('react-chartjs-2', () => ({
  Line: ({ data }) => (
    <div data-testid="trend-chart">
      {data.datasets.map((d) => (
        <span key={d.label} data-testid="series">
          {d.label}
        </span>
      ))}
    </div>
  ),
}))

async function setup() {
  await signIn('viewer')
  const expected = await getDashboard()
  renderPage(<DashboardPage />)
  await screen.findByTestId('card-current-stock')
  return expected
}

describe('DashboardPage', () => {
  it('shows the five summary cards from the mock (TC-DASH-01)', async () => {
    const { totals } = await setup()
    const cards = {
      'card-current-stock': String(totals.current_stock),
      'card-forecast-demand': String(totals.forecast_demand),
      'card-reorder': String(totals.reorder_count),
      'card-stockout': String(totals.stockout_count),
      'card-overstock': String(totals.overstock_count),
    }
    for (const [id, value] of Object.entries(cards)) {
      expect(within(screen.getByTestId(id)).getByText(value)).toBeInTheDocument()
    }
    expect(screen.getByText(/across 8 products/)).toBeInTheDocument()
    expect(screen.getByText(/Last updated/)).toBeInTheDocument()
    expect(screen.getByText(/mock data until the forecasting API/)).toBeInTheDocument()
  })

  it('lists every at-risk item with its risk type (TC-DASH-02)', async () => {
    const { items } = await setup()
    const risky = items.filter((i) => i.risk !== 'none')
    expect(risky.length).toBeGreaterThan(0)
    for (const i of risky) {
      const row = screen.getByText(i.sku).closest('tr')
      const label = i.risk === 'stockout' ? 'Stockout' : 'Overstock'
      expect(within(row).getByText(label)).toBeInTheDocument()
    }
    for (const i of items.filter((x) => x.risk === 'none')) {
      expect(screen.queryByText(i.sku)).not.toBeInTheDocument()
    }
  })

  it('narrows rows with the filter buttons', async () => {
    const user = userEvent.setup()
    const { items } = await setup()
    const over = items.filter((i) => i.risk === 'overstock')
    const stock = items.filter((i) => i.risk === 'stockout')
    await user.click(screen.getByRole('button', { name: 'Overstock' }))
    for (const i of over) expect(screen.getByText(i.sku)).toBeInTheDocument()
    for (const i of stock) expect(screen.queryByText(i.sku)).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Stockout' }))
    for (const i of stock) expect(screen.getByText(i.sku)).toBeInTheDocument()
    for (const i of over) expect(screen.queryByText(i.sku)).not.toBeInTheDocument()
  })

  it('passes both series to the chart', async () => {
    await setup()
    expect(screen.getByTestId('trend-chart')).toBeInTheDocument()
    const labels = screen.getAllByTestId('series').map((e) => e.textContent)
    expect(labels).toEqual(['Actual sales', 'Forecast'])
  })
})
