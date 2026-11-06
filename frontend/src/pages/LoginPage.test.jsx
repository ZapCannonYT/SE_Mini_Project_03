import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../auth/AuthContext.jsx'
import LoginPage from './LoginPage.jsx'

function setup() {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<div>dashboard page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  )
}

describe('LoginPage', () => {
  it('shows validation messages on empty submit', async () => {
    const user = userEvent.setup()
    setup()
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    expect(screen.getByText('Email is required')).toBeInTheDocument()
    expect(screen.getByText('Password is required')).toBeInTheDocument()
  })

  it('shows invalid email message', async () => {
    const user = userEvent.setup()
    setup()
    await user.type(screen.getByLabelText('Email'), 'nope')
    await user.type(screen.getByLabelText('Password'), 'x')
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    expect(screen.getByText('Enter a valid email')).toBeInTheDocument()
  })

  it('shows a server error for bad credentials', async () => {
    const user = userEvent.setup()
    setup()
    await user.type(screen.getByLabelText('Email'), 'admin@dfip.local')
    await user.type(screen.getByLabelText('Password'), 'wrong')
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    expect(await screen.findByText('Invalid email or password')).toBeInTheDocument()
  })

  it('redirects to the dashboard after successful mock login', async () => {
    const user = userEvent.setup()
    setup()
    await user.type(screen.getByLabelText('Email'), 'admin@dfip.local')
    await user.type(screen.getByLabelText('Password'), 'password123')
    await user.click(screen.getByRole('button', { name: /sign in/i }))
    await waitFor(() => expect(screen.getByText('dashboard page')).toBeInTheDocument())
  })
})
