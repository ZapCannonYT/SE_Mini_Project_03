export default function PlaceholderPage({ title, description }) {
  return (
    <section>
      <div className="page-header">
        <h1>{title}</h1>
      </div>
      <div className="card">
        <p>{description}</p>
        <p className="muted">This page is a placeholder and will be built in a later story.</p>
      </div>
    </section>
  )
}
