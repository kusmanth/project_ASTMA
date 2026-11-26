// Small helpers shared by all the add / edit forms

export const canEdit = (user) => ["admin", "police"].includes(user?.user_type);

export function Field({ label, children, wide }) {
  return (
    <label className={`field ${wide ? "wide" : ""}`}>
      <span>{label}</span>
      {children}
    </label>
  );
}

// A panel with a title, the form fields, and Save / Cancel buttons
export function FormPanel({ title, onSubmit, onCancel, busy, error, children, submitLabel = "Save" }) {
  return (
    <form
      className="panel form-panel"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <h3>{title}</h3>
      <div className="form-grid">{children}</div>
      {error && <div className="alert error">{error}</div>}
      <div className="actions">
        <button type="submit" disabled={busy}>{busy ? "Saving..." : submitLabel}</button>
        <button type="button" className="ghost" onClick={onCancel} disabled={busy}>Cancel</button>
      </div>
    </form>
  );
}

export function ViewOnlyNote() {
  return <p className="muted small view-only">View only. Sign in as Admin or Police to add or edit.</p>;
}
