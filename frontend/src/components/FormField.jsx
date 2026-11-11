// Reusable label + control + error text. Renders an <input> by default, or a
// <select> when `as="select"` (pass the <option> elements as children).
export default function FormField({ id, label, error, hint, as = 'input', children, ...props }) {
  const errorId = `${id}-error`
  const hintId = `${id}-hint`
  const describedBy = [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(' ')
  const Control = as
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <Control
        id={id}
        aria-invalid={!!error}
        aria-describedby={describedBy || undefined}
        {...props}
      >
        {children}
      </Control>
      {hint && (
        <div id={hintId} className="muted field-hint">
          {hint}
        </div>
      )}
      {error && (
        <div id={errorId} className="field-error">
          {error}
        </div>
      )}
    </div>
  )
}
