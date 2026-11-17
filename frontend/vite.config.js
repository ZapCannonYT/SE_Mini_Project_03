import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// HTTPS dev mode (SR-005): `npm run dev:https` serves the site over TLS with the self-signed
// certificate from scripts/make_dev_cert.py and proxies /api to the HTTPS backend.
export default defineConfig(({ mode }) => {
  const useHttps = mode === 'https'
  const certDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../certs')
  const https = useHttps
    ? {
        key: fs.readFileSync(path.join(certDir, 'dev.key')),
        cert: fs.readFileSync(path.join(certDir, 'dev.crt')),
      }
    : undefined
  const target = useHttps ? 'https://localhost:8000' : 'http://localhost:8000'
  return {
    plugins: [react()],
    server: {
      https,
      proxy: {
        '/api': { target, secure: false },
        '/health': { target, secure: false },
      },
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: './src/test/setup.js',
    },
  }
})
