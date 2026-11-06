import { NavLink, Outlet } from 'react-router-dom'
import { useAuth, hasRole } from '../auth/AuthContext.jsx'
import { isMockMode } from '../api/client.js'

const NAV = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/products', label: 'Products' },
  { to: '/inventory', label: 'Inventory' },
  { to: '/sales', label: 'Sales' },
  { to: '/forecasts', label: 'Forecasts' },
  { to: '/planning', label: 'Planning' },
  { to: '/reports', label: 'Reports' },
  { to: '/admin', label: 'Admin', adminOnly: true },
]

export default function Layout() {
  const { user, logout } = useAuth()
  const items = NAV.filter((n) => !n.adminOnly || hasRole(user, 'admin'))

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-title">DFIP</div>
          <div className="brand-subtitle">Demand Forecasting &amp; Inventory Planning</div>
        </div>
        <nav aria-label="Main navigation" className="nav">
          {items.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="main-column">
        <header className="app-header">
          <div className="header-user">
            <span className="header-email">{user?.email}</span>
            <span className="badge badge-role">{user?.role}</span>
            {isMockMode() && <span className="badge badge-mock">Mock data</span>}
          </div>
          <button type="button" className="btn btn-secondary" onClick={logout}>
            Log out
          </button>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
