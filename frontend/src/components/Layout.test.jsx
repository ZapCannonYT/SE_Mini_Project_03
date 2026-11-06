import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../auth/AuthContext.jsx'
import { setAuth } from '../auth/storage.js'
import Layout from './Layout.jsx'

function setup(role) {
  setAuth({ token: 'mock-token-1', role, email: `${role}@dfip.local` })
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route element={<Layout />}>
            <Route path="dashboard" element={<div>page body</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('Layout', () => {
  it('shows all 8 nav items for admin, in order', () => {
    setup('admin')
    const links = screen.getAllByRole('link').map((a) => a.textContent)
    expect(links).toEqual([
      'Dashboard',
      'Products',
      'Inventory',
      'Sales',
      'Forecasts',
      'Planning',
      'Reports',
      'Admin',
    ])
    expect(screen.getByText('Mock data')).toBeInTheDocument()
    expect(screen.getByText('admin@dfip.local')).toBeInTheDocument()
    expect(screen.getByText('page body')).toBeInTheDocument()
  })

  it('hides Admin for viewer', () => {
    setup('viewer')
    expect(screen.queryByRole('link', { name: 'Admin' })).not.toBeInTheDocument()
    expect(screen.getAllByRole('link')).toHaveLength(7)
  })
})
