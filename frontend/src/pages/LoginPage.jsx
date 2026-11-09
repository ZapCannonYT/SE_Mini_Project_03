import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'
import { isMockMode } from '../api/client.js'

function validate(email, password) {
  const errors = {}
  if (!email.trim()) errors.email = 'Email is required'
  else if (!/^[^@\s]+@[^@\s]+$/.test(email.trim())) errors.email = 'Enter a valid email'
  if (!password) errors.password = 'Password is required'
  return errors
}

export default function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (isAuthenticated && !submitting) return <Navigate to="/dashboard" replace />

  const from = location.state?.from
  const target = from ? `${from.pathname || '/dashboard'}${from.search || ''}` : '/dashboard'

  async function onSubmit(e) {
    e.preventDefault()
    setServerError('')
    const found = validate(email, password)
    setErrors(found)
    if (Object.keys(found).length) return
    setSubmitting(true)
    try {
      await login(email.trim(), password)
      navigate(target, { replace: true })
    } catch (err) {
      setServerError(err.message || 'Login failed')
      setSubmitting(false)
    }
  }

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1 className="login-title">DFIP</h1>
        <p className="muted">Sign in to continue</p>
        <div role="alert">
          {serverError && <div className="alert alert-error">{serverError}</div>}
        </div>
        <form className="form" onSubmit={onSubmit} noValidate>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-invalid={!!errors.email}
            />
            {errors.email && <div className="field-error">{errors.email}</div>}
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              aria-invalid={!!errors.password}
            />
            {errors.password && <div className="field-error">{errors.password}</div>}
          </div>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
        {isMockMode() && (
          <div className="mock-note">
            <strong>Mock mode demo accounts</strong>
            <ul>
              <li>admin@dfip.local</li>
              <li>planner@dfip.local</li>
              <li>viewer@dfip.local</li>
            </ul>
            <div>
              Password: <code>password123</code>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
