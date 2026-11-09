const KEY = 'dfip.auth'

export function getAuth() {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return null
    const data = JSON.parse(raw)
    return data && data.token ? data : null
  } catch {
    return null
  }
}

export function getToken() {
  const auth = getAuth()
  return auth ? auth.token : null
}

export function setAuth({ token, role, email }) {
  try {
    localStorage.setItem(KEY, JSON.stringify({ token, role, email }))
  } catch {
    // storage unavailable; session will not persist
  }
}

export function clearAuth() {
  try {
    localStorage.removeItem(KEY)
  } catch {
    // ignore
  }
}
