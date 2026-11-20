import { useEffect, useState } from "react";
import { api } from "../api.js";
import PageHead from "../components/PageHead.jsx";

const URGENCY_CLASS = { critical: "high", normal: "medium", none: "none" };
const STATUS_CLASS = { active: "low", completed: "none", cancelled: "high" };
const time = (t) => (t ? t.replace("T", " ").slice(5, 16) : "-");

export default function Trips({ user, junctions, go }) {
  const [trips, setTrips] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [filter, setFilter] = useState("active");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ vehicle_id: "", from: "", to: "", urgency_level: "critical" });

  async function load() {
    try {
      const [t, v] = await Promise.all([api.trips(), api.vehicles()]);
      setTrips([...t].sort((a, b) => b.id - a.id));
      setVehicles(v);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }
  useEffect(() => { load(); }, []);

  // Sensible defaults for the form once data arrives
  useEffect(() => {
    if (vehicles.length && !form.vehicle_id) setForm((f) => ({ ...f, vehicle_id: String(vehicles[0].id) }));
  }, [vehicles]);
  useEffect(() => {
    if (junctions.length >= 2 && !form.from)
      setForm((f) => ({ ...f, from: String(junctions[0].id), to: String(junctions[junctions.length - 1].id) }));
  }, [junctions]);

  const junction = (id) => junctions.find((j) => j.id === id)?.junction_name || `Junction ${id}`;
  const vehicle = (id) => vehicles.find((v) => v.id === id);
  const count = (s) => trips.filter((t) => t.status === s).length;
  const shown = filter === "all" ? trips : trips.filter((t) => t.status === filter);

  async function act(action, message) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
      setNotice(message);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function createTrip(e) {
    e.preventDefault();
    act(async () => {
      const trip = await api.createTrip({
        vehicle_id: Number(form.vehicle_id),
        created_by: user.id,
        from_junction_id: Number(form.from),
        to_junction_id: Number(form.to),
        urgency_level: form.urgency_level,
      });
      setFilter("active");
      return trip;
    }, "New emergency trip started.");
  }

  return (
    <>
      <PageHead
        eyebrow="Emergency management"
        title="Emergency trips"
        text="Every ambulance, fire truck or police trip on the network. Start a trip, then mark it completed when it arrives."
      >
        <button className="ghost" onClick={() => go("assistant")}>Book with AI instead</button>
      </PageHead>

      <div className="tiles three">
        <div className="tile"><span className="badge low">active</span><b>{count("active")}</b><small>on the road now</small></div>
        <div className="tile"><span className="badge none">completed</span><b>{count("completed")}</b><small>reached destination</small></div>
        <div className="tile"><span className="badge high">cancelled</span><b>{count("cancelled")}</b><small>stopped early</small></div>
      </div>

      <form className="panel" onSubmit={createTrip}>
        <h3>Start a new trip</h3>
        <div className="form-row">
          <label>
            Vehicle
            <select value={form.vehicle_id} onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })}>
              {vehicles.map((v) => <option key={v.id} value={v.id}>{v.vehicle_number} ({v.vehicle_type.replace("_", " ")})</option>)}
            </select>
          </label>
          <label>
            From
            <select value={form.from} onChange={(e) => setForm({ ...form, from: e.target.value })}>
              {junctions.map((j) => <option key={j.id} value={j.id}>{j.junction_name}</option>)}
            </select>
          </label>
          <label>
            To
            <select value={form.to} onChange={(e) => setForm({ ...form, to: e.target.value })}>
              {junctions.map((j) => <option key={j.id} value={j.id}>{j.junction_name}</option>)}
            </select>
          </label>
          <label>
            Urgency
            <select value={form.urgency_level} onChange={(e) => setForm({ ...form, urgency_level: e.target.value })}>
              <option value="critical">Critical</option>
              <option value="normal">Normal</option>
              <option value="none">None</option>
            </select>
          </label>
          <button type="submit" disabled={busy || !form.vehicle_id}>Start trip</button>
        </div>
      </form>

      {notice && <div className="alert ok">{notice}</div>}
      {error && <div className="alert error">{error}</div>}

      <div className="panel">
        <div className="tabs">
          {["active", "completed", "cancelled", "all"].map((f) => (
            <button key={f} className={`tab ${filter === f ? "on" : ""}`} onClick={() => setFilter(f)}>
              {f} {f !== "all" && <span>{count(f)}</span>}
            </button>
          ))}
        </div>

        {shown.length === 0 ? (
          <p className="muted">No {filter === "all" ? "" : filter} trips.</p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr><th>Trip</th><th>Vehicle</th><th>Route</th><th>Urgency</th><th>Status</th><th>Started</th><th>Ended</th><th></th></tr>
              </thead>
              <tbody>
                {shown.map((t) => (
                  <tr key={t.id}>
                    <td>#{t.id}</td>
                    <td>
                      <b>{vehicle(t.vehicle_id)?.vehicle_number || `Vehicle ${t.vehicle_id}`}</b>
                      <div className="muted small">{vehicle(t.vehicle_id)?.vehicle_type.replace("_", " ")}</div>
                    </td>
                    <td>{junction(t.from_junction_id)} → {junction(t.to_junction_id)}</td>
                    <td><span className={`badge ${URGENCY_CLASS[t.urgency_level] || "none"}`}>{t.urgency_level}</span></td>
                    <td><span className={`badge ${STATUS_CLASS[t.status] || "none"}`}>{t.status}</span></td>
                    <td className="muted">{time(t.start_time)}</td>
                    <td className="muted">{time(t.end_time)}</td>
                    <td>
                      {t.status === "active" && (
                        <div className="row-actions">
                          <button className="small-btn" disabled={busy}
                            onClick={() => act(() => api.setTripStatus(t.id, "completed"), `Trip #${t.id} marked completed.`)}>
                            Complete
                          </button>
                          <button className="small-btn ghost" disabled={busy}
                            onClick={() => act(() => api.setTripStatus(t.id, "cancelled"), `Trip #${t.id} cancelled.`)}>
                            Cancel
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
