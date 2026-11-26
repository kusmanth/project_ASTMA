import { useEffect, useState } from "react";
import { api } from "../api.js";
import PageHead from "../components/PageHead.jsx";
import useAction from "../components/useAction.js";
import { TrafficTable, StatusBadge } from "../components/ResultView.jsx";
import { Field, FormPanel, canEdit } from "../components/Form.jsx";

const EMPTY = { road_id: "", two_wheeler_count: 20, three_wheeler_count: 5, four_wheeler_count: 15, heavy_vehicle_count: 2, average_speed: 30 };

// Same formula as the Traffic Monitoring agent, so the user sees the level before saving
function density(v, lanes) {
  const weighted = v.two_wheeler_count * 0.5 + Number(v.three_wheeler_count) + Number(v.four_wheeler_count) + v.heavy_vehicle_count * 3;
  return lanes ? weighted / lanes : 0;
}
const level = (d) => (d < 10 ? "low" : d <= 20 ? "medium" : "high");

export default function Monitoring({ user, roads }) {
  const [state, run] = useAction();
  const [form, setForm] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  useEffect(() => { run(api.trafficMonitoring); }, []);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));
  const road = form && roads.find((r) => r.id === Number(form.road_id));
  const d = form ? density(form, road?.lanes) : 0;

  async function save() {
    setBusy(true);
    setError("");
    try {
      const reading = Object.fromEntries(Object.entries(form).map(([k, v]) => [k, Number(v)]));
      await api.createReading({ ...reading, congestion_level: level(d) });
      setNotice(`Reading saved for ${road?.road_name}. The table below is updated.`);
      setForm(null);
      run(api.trafficMonitoring);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead
        eyebrow="Agent · Traffic Monitoring"
        title="Live traffic"
        text="Uses each road's latest reading from the last 15 minutes and rates the congestion."
      >
        <div className="actions">
          {canEdit(user) && !form && (
            <button className="ghost" onClick={() => { setNotice(""); setForm({ ...EMPTY, road_id: String(roads[0]?.id || "") }); }}>
              + Add traffic reading
            </button>
          )}
          <button onClick={() => run(api.trafficMonitoring)} disabled={state.busy}>{state.busy ? "Checking..." : "Check again"}</button>
        </div>
      </PageHead>

      {form && (
        <FormPanel title="Add a traffic reading" onSubmit={save} onCancel={() => setForm(null)} busy={busy} error={error} submitLabel="Save reading">
          <Field label="Road" wide>
            <select value={form.road_id} onChange={set("road_id")}>
              {roads.map((r) => <option key={r.id} value={r.id}>{r.road_name} ({r.lanes} lanes)</option>)}
            </select>
          </Field>
          <Field label="Two-wheelers"><input type="number" min="0" value={form.two_wheeler_count} onChange={set("two_wheeler_count")} required /></Field>
          <Field label="Three-wheelers"><input type="number" min="0" value={form.three_wheeler_count} onChange={set("three_wheeler_count")} required /></Field>
          <Field label="Cars"><input type="number" min="0" value={form.four_wheeler_count} onChange={set("four_wheeler_count")} required /></Field>
          <Field label="Heavy vehicles"><input type="number" min="0" value={form.heavy_vehicle_count} onChange={set("heavy_vehicle_count")} required /></Field>
          <Field label="Average speed (km/h)"><input type="number" min="0" step="0.1" value={form.average_speed} onChange={set("average_speed")} required /></Field>
          <div className="preview wide">
            Density <b>{d.toFixed(2)}</b> → <StatusBadge status={level(d)} />
          </div>
        </FormPanel>
      )}

      {notice && <div className="alert ok">{notice}</div>}
      <div className="panel">
        {state.error && <div className="alert error">{state.error}</div>}
        {state.data ? <TrafficTable reports={state.data.results} /> : !state.error && <p className="muted">Loading...</p>}
      </div>

      <div className="panel explain">
        <h3>How density is calculated</h3>
        <p className="formula">(bikes × 0.5 + autos + cars + heavy × 3) ÷ lanes</p>
        <div className="legend">
          <span><span className="badge low">low</span> under 10</span>
          <span><span className="badge medium">medium</span> 10 to 20</span>
          <span><span className="badge high">high</span> over 20</span>
        </div>
      </div>
    </>
  );
}
