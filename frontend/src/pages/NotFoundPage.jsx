import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <section>
      <div className="page-header">
        <h1>Page not found</h1>
      </div>
      <div className="card">
        <p>The page you are looking for does not exist.</p>
        <Link to="/dashboard">Back to dashboard</Link>
      </div>
    </section>
  )
}
