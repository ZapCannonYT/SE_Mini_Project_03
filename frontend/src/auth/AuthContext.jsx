import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import * as api from '../api/endpoints.js'
import { clearAuth, getAuth, setAuth } from './storage.js'

const AuthContext = createContext(null)

function readUser() {
  const a = getAuth()
  return a ? { email: a.email, role: a.role } : null
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(readUser)

  useEffect(() => {
    const onUnauthorized = () => {
      clearAuth()
      setUser(null)
    }
    window.addEventListener('dfip:unauthorized', onUnauthorized)
    return () => window.removeEventListener('dfip:unauthorized', onUnauthorized)
  }, [])

  const login = useCallback(async (email, password) => {
    const res = await api.login(email, password)
    setAuth({ token: res.access_token, role: res.role, email })
    setUser({ email, role: res.role })
    return res
  }, [])

  const logout = useCallback(async () => {
    try {
      await api.logout()
    } catch {
      // ignore: always clear local state
    }
    clearAuth()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, isAuthenticated: !!user, login, logout }),
    [user, login, logout],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

export function hasRole(user, ...roles) {
  return !!user && roles.includes(user.role)
}

export function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />
  return children
}
