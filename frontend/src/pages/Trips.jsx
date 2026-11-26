import { useEffect, useState } from "react";
import { api } from "../api.js";
import PageHead from "../components/PageHead.jsx";
import { reachableFrom } from "../components/reachable.js";

const URGENCY_CLASS = { critical: "high", normal: "medium", none: "none" };
const STATUS_CLASS = { active: "low", completed: "none", cancelled: "high" };
const time = (t) => (t ? t.replace("T", " ").slice(5, 16) : "-");

export default function Trips({ user, junctions, roads, go }) {
  const [trips, setTrips] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [filter, setFilter] = useState("active");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ vehicle_id: "", from: "", to: "", urgency_level: "critical" });

  async function load() {
    try {
      const [t, v, h] = await Promise.all([api.trips(), api.vehicles(), api.hospitals()]);
      setTrips([...t].sort((a, b) => b.id - a.id));
      setVehicles(v);
      setHospitals(h);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }
  useEffect(() => { load(); }, []);

  // Sensible defaults for the form once data arrives
  useEffect(() => {
    // Emergency drivers get their own vehicle selected first
    const mine = vehicles.find((v) => v.driver_id === user.id);
    if (vehicles.length && !form.vehicle_id) setForm((f) => ({ ...f, vehicle_id: String((mine || vehicles[0]).id) }));
  }, [vehicles]);
  // A hospital's vehicle always drives TO its hospital. Other vehicles can go anywhere.
  const selected = vehicles.find((v) => String(v.id) === form.vehicle_id);
  const hospital = hospitals.find((h) => h.id === selected?.hospital_id);
  const hospitalJunction = hospital?.nearest_junction_id;

  // "From": for a hospital vehicle, only places that have a road path to the hospital
  const starts = hospital
    ? junctions.filter((j) => j.id !== hospitalJunction && reachableFrom(j.id, roads).has(hospitalJunction))
    : junctions;
  // "To": the hospital, or every junction that roads connect to "From"
  const reachable = reachableFrom(form.from, roads);
  const destinations = hospital
    ? junctions.filter((j) => j.id === hospitalJunction)
    : junctions.filter((j) => reachable.has(j.id));

  useEffect(() => {
    if (!starts.some((j) => String(j.id) === form.from))
      setForm((f) => ({ ...f, from: starts.length ? String(starts[0].id) : "" }));
  }, [form.vehicle_id, junctions, roads, hospitals]);
  useEffect(() => {
    if (!destinations.some((j) => String(j.id) === form.to))
      setForm((f) => ({ ...f, to: destinations.length ? String(destinations[destinations.length - 1].id) : "" }));
  }, [form.from, form.vehicle_id, roads, hospitals]);

  const junction = (id) => junctions.find((j) => j.id === id)?.junction_name || `Junction ${id}`;
  const vehicle = (id) => vehicles.find((v) => v.id === id);
  const count = (s) => trips.filter((t) => t.status === s).length;
  const shown = filter === "all" ? trips : trips.filter((t) => t.status === filter);

  async function act(action, message) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const result = await action();
      setNotice(typeof message === "function" ? message(result) : message);
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
    }, (trip) => {
      const names = (trip.route || []).map((id) => roads.find((r) => r.id === id)?.road_name || `road ${id}`);
      return `Trip started. Green corridor: ${names.length} signals turned green (${names.join(" → ")}); cross traffic at those junctions is red.`;
    });
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
              {vehicles.map((v) => <option key={v.id} value={v.id}>{v.vehicle_number} ({v.vehicle_type.replace("_", " ")}){v.driver_id === user.id ? " · mine" : ""}</option>)}
            </select>
          </label>
          <label>
            From
            <select value={form.from} onChange={(e) => setForm({ ...form, from: e.target.value })}>
              {starts.map((j) => <option key={j.id} value={j.id}>{j.junction_name}</option>)}
            </select>
          </label>
          <label>
            {hospital ? `To (${hospital.hospital_name})` : "To"}
            <select value={form.to} disabled={!!hospital} onChange={(e) => setForm({ ...form, to: e.target.value })}>
              {destinations.length === 0 && <option value="">No road leads out of here</option>}
              {destinations.map((j) => <option key={j.id} value={j.id}>{j.junction_name}</option>)}
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
          <button type="submit" disabled={busy || !form.vehicle_id || !form.to}>Start trip</button>
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
