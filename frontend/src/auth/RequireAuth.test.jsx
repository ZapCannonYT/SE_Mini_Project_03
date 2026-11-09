import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider, RequireAuth } from './AuthContext.jsx'
import { setAuth } from './storage.js'

function setup() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/secret']}>
        <Routes>
          <Route path="/login" element={<div>login screen</div>} />
          <Route
            path="/secret"
            element={
              <RequireAuth>
                <div>secret content</div>
              </RequireAuth>
            }
          />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('RequireAuth', () => {
  it('redirects unauthenticated users to /login', () => {
    setup()
    expect(screen.getByText('login screen')).toBeInTheDocument()
    expect(screen.queryByText('secret content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    setAuth({ token: 'mock-token-1', role: 'admin', email: 'admin@dfip.local' })
    setup()
    expect(screen.getByText('secret content')).toBeInTheDocument()
  })
})
