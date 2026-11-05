import { render } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../auth/AuthContext.jsx'
import { login } from '../api/endpoints.js'
import { setAuth } from '../auth/storage.js'

export async function signIn(role) {
  const email = `${role}@dfip.local`
  const res = await login(email, 'password123')
  setAuth({ token: res.access_token, role: res.role, email })
}

export function renderPage(ui) {
  return render(
    <AuthProvider>
      <MemoryRouter>{ui}</MemoryRouter>
    </AuthProvider>,
  )
}
