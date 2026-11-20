import { useState } from "react";
import { api } from "../api.js";

const ROLES = [
  ["emergency_driver", "Emergency driver"],
  ["driver", "Driver"],
  ["police", "Traffic police"],
  ["admin", "Admin"],
];

export default function Login({ onLogin }) {
  const [mode, setMode] = useState("login"); // "login" or "register"
  const [form, setForm] = useState({ login: "", password: "", name: "", mobile: "", email: "", user_type: "emergency_driver" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") {
        await api.register({
          name: form.name,
          mobile: form.mobile,
          email: form.email || null,
          user_type: form.user_type,
          password: form.password,
        });
        onLogin(await api.login(form.mobile, form.password));
      } else {
        onLogin(await api.login(form.login, form.password));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-side">
        <div className="brand big">
          <div className="logo"><span /><span /><span /></div>
          <div>
            <b>ASTMA</b>
            <small>AI Smart Traffic Management Agent</small>
          </div>
        </div>
        <h1>Smarter signals.<br />Faster emergency routes.</h1>
        <ul className="login-points">
          <li>Ask the AI assistant in plain English</li>
          <li>Live congestion for every road</li>
          <li>Signals that adapt their green time</li>
          <li>Shortest routes for ambulances</li>
        </ul>
      </div>

      <form className="login-card" onSubmit={submit}>
        <h2>{mode === "login" ? "Sign in" : "Create account"}</h2>
        <p className="muted">{mode === "login" ? "Welcome back. Sign in to continue." : "Register a new ASTMA user."}</p>

        {mode === "login" ? (
          <label>
            Mobile number or email
            <input value={form.login} onChange={set("login")} placeholder="9876500001" required autoFocus />
          </label>
        ) : (
          <>
            <label>Full name<input value={form.name} onChange={set("name")} minLength={4} required autoFocus /></label>
            <label>Mobile number<input value={form.mobile} onChange={set("mobile")} pattern="\d{10}" title="10 digits" required /></label>
            <label>Email (optional)<input type="email" value={form.email} onChange={set("email")} /></label>
            <label>
              Role
              <select value={form.user_type} onChange={set("user_type")}>
                {ROLES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </label>
          </>
        )}

        <label>
          Password
          <input type="password" value={form.password} onChange={set("password")} minLength={mode === "register" ? 8 : 1} required />
        </label>

        {error && <div className="alert error">{error}</div>}

        <button type="submit" disabled={busy}>{busy ? "Please wait..." : mode === "login" ? "Sign in" : "Create account"}</button>

        <p className="switch">
          {mode === "login" ? "New here?" : "Already have an account?"}{" "}
          <a href="#" onClick={(e) => { e.preventDefault(); setError(""); setMode(mode === "login" ? "register" : "login"); }}>
            {mode === "login" ? "Create an account" : "Sign in"}
          </a>
        </p>
        {mode === "login" && <p className="muted small hint">Demo login: 9876500001 / demo12345</p>}
      </form>
    </div>
  );
}
