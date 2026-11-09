# DFIP Frontend

Web UI / Dashboard for the Demand Forecasting & Inventory Planning system (SAD 3.4): login, data-entry forms, forecast and planning views, alerts and reports.

## Stack

- Vite + React (plain JavaScript)
- react-router-dom v6
- Vitest, Testing Library, jsdom

## Getting started

```
npm install
npm run dev
```

The app is served at http://localhost:5173. The dev server proxies `/api` and `/health` to the backend on http://localhost:8000 (the backend has no CORS configuration, so always go through the proxy).

## Mock mode vs real API

Mock mode is ON unless `VITE_USE_MOCK` is exactly `false`. In mock mode no network calls are made; an in-memory fake backend (`src/api/mock.js`) answers every request with about 250ms latency and mirrors the real API's roles, validation rules and error shapes. Data resets on page reload.

To use the real backend, copy the example env file and turn mock mode off:

```
cp .env.example .env.local
# edit .env.local: VITE_USE_MOCK=false
```

`VITE_API_BASE_URL` stays empty to use the same origin via the Vite proxy.

### Demo mock accounts

These exist only in the in-browser mock and are not real credentials.

| Email | Role |
| --- | --- |
| admin@dfip.local | admin |
| planner@dfip.local | planner |
| viewer@dfip.local | viewer |

Mock password for all three: `password123`.

## Scripts

- `npm run dev` - start the dev server
- `npm run build` - production build into `dist/`
- `npm run preview` - serve the production build
- `npm test` - run the Vitest suite (watch mode; use `npm test -- --run` for a single run)

## Folder layout

```
frontend/
  index.html
  vite.config.js         Vite, dev proxy and Vitest config
  .env.example
  src/
    main.jsx             entry point
    App.jsx              routes
    styles.css           global styles and shared classes
    api/
      client.js          fetch wrapper, ApiError, mock switch
      endpoints.js       named API functions
      mock.js            in-memory mock backend (route table)
    auth/
      storage.js         localStorage helpers
      AuthContext.jsx    AuthProvider, useAuth, RequireAuth, hasRole
    components/
      Layout.jsx         sidebar, header, outlet
    pages/
      LoginPage.jsx
      PlaceholderPage.jsx
      NotFoundPage.jsx
    test/
      setup.js           Vitest setup (jest-dom, mock reset)
```
