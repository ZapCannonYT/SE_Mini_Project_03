import { fireEvent, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderPage, signIn } from '../test/helpers.jsx'
import SalesPage from './SalesPage.jsx'

async function setupAs(role) {
  await signIn(role)
  renderPage(<SalesPage />)
  await screen.findByText(/\d+ records/)
}

function futureDate() {
  const d = new Date()
  d.setDate(d.getDate() + 3)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function csvFile(text, name = 'sales.csv') {
  return new File([text], name, { type: 'text/csv' })
}

describe('SalesPage', () => {
  it('validates the add sale form', async () => {
    const user = userEvent.setup()
    await setupAs('planner')
    await user.click(screen.getByRole('button', { name: 'Add sale' }))
    expect(screen.getByText('Product is required')).toBeInTheDocument()
    expect(screen.getByText('Date is required')).toBeInTheDocument()
    expect(screen.getByText('Quantity sold is required')).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText('Product'), '1')
    fireEvent.change(screen.getByLabelText('Date'), { target: { value: futureDate() } })
    await user.type(screen.getByLabelText('Quantity sold'), '-4')
    await user.click(screen.getByRole('button', { name: 'Add sale' }))
    expect(screen.getByText('Date cannot be in the future')).toBeInTheDocument()
    expect(screen.getByText('Quantity sold cannot be negative')).toBeInTheDocument()
  })

  it('shows a conflict when the sale already exists', async () => {
    const user = userEvent.setup()
    await setupAs('admin')
    const cells = within(screen.getAllByRole('row')[1]).getAllByRole('cell')
    const firstDate = cells[0].textContent
    const firstSku = cells[1].textContent
    const select = screen.getByLabelText('Product')
    const option = [...select.options].find((o) => o.textContent.startsWith(firstSku))
    await user.selectOptions(select, option.value)
    fireEvent.change(screen.getByLabelText('Date'), { target: { value: firstDate } })
    await user.type(screen.getByLabelText('Quantity sold'), '5')
    await user.click(screen.getByRole('button', { name: 'Add sale' }))
    expect(await screen.findByText(/already exists/i)).toBeInTheDocument()
  })

  it('filters the table by product', async () => {
    const user = userEvent.setup()
    await setupAs('admin')
    await user.selectOptions(screen.getByLabelText('Filter by product'), '2')
    await user.click(screen.getByRole('button', { name: 'Apply' }))
    expect(await screen.findByText('60 records')).toBeInTheDocument()
    const rows = screen.getAllByRole('row').slice(1)
    expect(rows.every((r) => within(r).queryByText('SKU-1002'))).toBe(true)
  })

  it('validates the date range filter', async () => {
    const user = userEvent.setup()
    await setupAs('viewer')
    fireEvent.change(screen.getByLabelText('Start date'), { target: { value: '2026-02-10' } })
    fireEvent.change(screen.getByLabelText('End date'), { target: { value: '2026-02-01' } })
    await user.click(screen.getByRole('button', { name: 'Apply' }))
    expect(screen.getByText('Start date must be on or before end date')).toBeInTheDocument()
  })

  it('hides add and import sections for viewers', async () => {
    await setupAs('viewer')
    expect(screen.queryByRole('button', { name: 'Add sale' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Upload' })).not.toBeInTheDocument()
  })

  it('reports imported and rejected rows for a mixed file', async () => {
    const user = userEvent.setup()
    await setupAs('planner')
    const csv = [
      'sku,date,quantity_sold',
      'SKU-1001,2020-01-01,5',
      'NOPE,2020-01-01,5',
      'SKU-1002,2020-01-01,abc',
    ].join('\n')
    await user.upload(screen.getByLabelText('CSV file'), csvFile(csv))
    await user.click(screen.getByRole('button', { name: 'Upload' }))
    expect(await screen.findByText('1 rows imported')).toBeInTheDocument()
    expect(screen.getByText('Unknown SKU: NOPE')).toBeInTheDocument()
    expect(screen.getByText('Quantity sold must be a whole number')).toBeInTheDocument()
  })

  it('rejects a file with the wrong header', async () => {
    const user = userEvent.setup()
    await setupAs('admin')
    await user.upload(screen.getByLabelText('CSV file'), csvFile('a,b,c\n1,2,3'))
    await user.click(screen.getByRole('button', { name: 'Upload' }))
    expect(await screen.findByText(/Header must be exactly/)).toBeInTheDocument()
  })

  it('requires a .csv file', async () => {
    const user = userEvent.setup({ applyAccept: false })
    await setupAs('admin')
    await user.click(screen.getByRole('button', { name: 'Upload' }))
    expect(screen.getByText('Choose a CSV file to upload')).toBeInTheDocument()
    await user.upload(screen.getByLabelText('CSV file'), csvFile('x', 'sales.txt'))
    await user.click(screen.getByRole('button', { name: 'Upload' }))
    expect(screen.getByText('File must be a .csv file')).toBeInTheDocument()
  })
})
