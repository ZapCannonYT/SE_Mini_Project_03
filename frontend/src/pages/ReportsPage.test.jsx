import { screen, within, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { renderPage, signIn } from '../test/helpers.jsx'
import { getPlanningReport } from '../api/endpoints.js'
import ReportsPage from './ReportsPage.jsx'

async function setup(role = 'viewer') {
  await signIn(role)
  const user = userEvent.setup()
  renderPage(<ReportsPage />)
  await screen.findByText(/^\d+ rows?$/)
  return user
}

function tableSkus() {
  const body = screen.getAllByRole('rowgroup')[1]
  return within(body)
    .queryAllByRole('row')
    .map((r) => within(r).queryAllByRole('cell')[1]?.textContent)
    .filter(Boolean)
}

describe('ReportsPage', () => {
  it('lists the planning report with the inputs used (TC-RPT-01)', async () => {
    await setup()
    const all = await getPlanningReport()
    expect(all.length).toBeGreaterThan(1)
    expect(screen.getByText(`${all.length} rows`)).toBeInTheDocument()
    const first = all[0]
    const row = screen.getByText(first.sku).closest('tr')
    expect(within(row).getByText(first.name)).toBeInTheDocument()
    expect(within(screen.getByRole('table')).getByText('Safety stock')).toBeInTheDocument()
  })

  it('filters by product and by risk (TC-RPT-01)', async () => {
    const user = await setup()
    const all = await getPlanningReport()
    const target = all[2]
    await user.selectOptions(screen.getByLabelText('Product'), String(target.product_id))
    await user.click(screen.getByRole('button', { name: 'Apply' }))
    await screen.findByText('1 row')
    expect(tableSkus()).toEqual([target.sku])

    await user.click(screen.getByRole('button', { name: 'Clear' }))
    await screen.findByText(`${all.length} rows`)
    const stockouts = all.filter((r) => r.risk === 'stockout')
    await user.selectOptions(screen.getByLabelText('Risk'), 'stockout')
    await user.click(screen.getByRole('button', { name: 'Apply' }))
    await screen.findByText(`${stockouts.length} ${stockouts.length === 1 ? 'row' : 'rows'}`)
    expect(tableSkus().sort()).toEqual(stockouts.map((r) => r.sku).sort())
  })

  it('shows an empty state when the dates exclude every row', async () => {
    const user = await setup()
    await user.type(screen.getByLabelText('From date'), '2999-01-01')
    await user.click(screen.getByRole('button', { name: 'Apply' }))
    expect(await screen.findByText('No recommendations match these filters.')).toBeInTheDocument()
    expect(screen.getByText('0 rows')).toBeInTheDocument()
  })

  it('rejects a start date after the end date without calling the API', async () => {
    const user = await setup()
    await user.type(screen.getByLabelText('From date'), '2026-05-10')
    await user.type(screen.getByLabelText('To date'), '2026-05-01')
    await user.click(screen.getByRole('button', { name: 'Apply' }))
    expect(screen.getByText('Start date must be on or before end date')).toBeInTheDocument()
  })

  it('exports a CSV with the same rows as the filtered table (TC-RPT-02)', async () => {
    const user = await setup()
    const all = await getPlanningReport()
    const overstock = all.filter((r) => r.risk === 'overstock')
    await user.selectOptions(screen.getByLabelText('Risk'), 'overstock')
    await user.click(screen.getByRole('button', { name: 'Apply' }))
    await screen.findByText(`${overstock.length} ${overstock.length === 1 ? 'row' : 'rows'}`)
    const shownSkus = tableSkus()

    let blob
    URL.createObjectURL = vi.fn((b) => {
      blob = b
      return 'blob:report'
    })
    URL.revokeObjectURL = vi.fn()
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    await user.click(screen.getByRole('button', { name: 'Export CSV' }))
    await waitFor(() => expect(click).toHaveBeenCalled())

    const lines = (await blob.text()).trim().split('\r\n')
    const header = lines[0].split(',')
    expect(header.slice(0, 3)).toEqual(['recommendation_id', 'sku', 'name'])
    const csvSkus = lines
      .slice(1)
      .map((l) => l.split(',')[header.indexOf('sku')].replaceAll('"', ''))
    expect(csvSkus).toEqual(shownSkus)
    expect(csvSkus.length).toBe(overstock.length)
    click.mockRestore()
  })

  it('shows an error when the report cannot be loaded', async () => {
    renderPage(<ReportsPage />)
    expect(await screen.findByText(/not authenticated/i)).toBeInTheDocument()
  })
})
