import '@testing-library/jest-dom/vitest'
import { vi, beforeEach } from 'vitest'
import { resetMockDb } from '../api/mock.js'

vi.stubEnv('VITE_USE_MOCK', 'true')

// Newer Node versions ship an experimental global localStorage that can shadow
// jsdom's and lacks a working API. Install a simple in-memory one if needed.
if (typeof globalThis.localStorage?.clear !== 'function') {
  const store = new Map()
  const memoryStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => void store.set(k, String(v)),
    removeItem: (k) => void store.delete(k),
    clear: () => store.clear(),
    key: (i) => [...store.keys()][i] ?? null,
    get length() {
      return store.size
    },
  }
  Object.defineProperty(globalThis, 'localStorage', { value: memoryStorage, configurable: true })
  Object.defineProperty(window, 'localStorage', { value: memoryStorage, configurable: true })
}

beforeEach(() => {
  resetMockDb()
  localStorage.clear()
})
