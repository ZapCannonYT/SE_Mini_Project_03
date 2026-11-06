import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from './AuthContext.jsx'
import { getToken } from './storage.js'

function Probe() {
  const { user, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="who">{user ? `${user.email}:${user.role}` : 'anon'}</span>
      <button onClick={() => login('planner@dfip.local', 'password123')}>in</button>
      <button onClick={() => logout()}>out</button>
    </div>
  )
}

describe('AuthContext', () => {
  it('login stores the token and logout clears it', async () => {
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    )
    expect(screen.getByTestId('who')).toHaveTextContent('anon')
    await user.click(screen.getByText('in'))
    await waitFor(() =>
      expect(screen.getByTestId('who')).toHaveTextContent('planner@dfip.local:planner'),
    )
    expect(getToken()).toBe('mock-token-2')
    await user.click(screen.getByText('out'))
    await waitFor(() => expect(screen.getByTestId('who')).toHaveTextContent('anon'))
    expect(getToken()).toBeNull()
  })
})
