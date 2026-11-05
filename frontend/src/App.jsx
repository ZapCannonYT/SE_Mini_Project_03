import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth, useAuth, hasRole } from './auth/AuthContext.jsx'
import Layout from './components/Layout.jsx'
import LoginPage from './pages/LoginPage.jsx'
import PlaceholderPage from './pages/PlaceholderPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'

const PAGES = [
  ['dashboard', 'Dashboard', 'Key stock, forecast and alert indicators will appear here.'],
  ['products', 'Products', 'The product catalogue with create, edit and deactivate actions will appear here.'],
  ['inventory', 'Inventory', 'Current stock levels per product and quantity updates will appear here.'],
  ['sales', 'Sales', 'Sales history entry and import will appear here.'],
  ['forecasts', 'Forecasts', 'Demand forecasts per product and horizon will appear here.'],
  ['planning', 'Planning', 'Reorder and overstock planning recommendations will appear here.'],
  ['reports', 'Reports', 'Downloadable inventory and forecast reports will appear here.'],
]

function AdminOnly({ children }) {
  const { user } = useAuth()
  if (!hasRole(user, 'admin')) {
    return (
      <section>
        <div className="page-header">
          <h1>Admin</h1>
        </div>
        <div className="alert alert-error">You do not have access to this page</div>
      </section>
    )
  }
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          {PAGES.map(([path, title, desc]) => (
            <Route
              key={path}
              path={path}
              element={<PlaceholderPage title={title} description={desc} />}
            />
          ))}
          <Route
            path="admin"
            element={
              <AdminOnly>
                <PlaceholderPage
                  title="Admin"
                  description="User management, including creating users and changing roles, will appear here."
                />
              </AdminOnly>
            }
          />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
