import { useEffect, useState } from "react";
import { api } from "../api.js";
import PageHead from "../components/PageHead.jsx";
import useAction from "../components/useAction.js";
import { Field, FormPanel, ViewOnlyNote, canEdit } from "../components/Form.jsx";

async function loadSignals() {
  const [signals, timings] = await Promise.all([api.signals(), api.signalTimings()]);
  return { signals, timings };
}

const NEW_SIGNAL = { junction_id: "", road_id: "", green_time: 45, yellow_time: 5, red_time: 60 };

// Badge colour for the light each signal is showing right now (green during an emergency corridor)
const LIGHT = { green: "low", yellow: "medium", red: "high" };

export default function Signals({ user, roads, junctions }) {
  const [state, run] = useAction();
  const [message, setMessage] = useState("");
  const [form, setForm] = useState(null); // { mode: "add" | "edit", timing?, values }
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const editable = canEdit(user);
  useEffect(() => { run(loadSignals); }, []);

  // Live lights: ask the backend every 2 seconds what each light shows right now
  const [live, setLive] = useState([]);
  useEffect(() => {
    let stop = false;
    const tick = () => api.liveSignals().then((d) => { if (!stop) setLive(d); }).catch(() => {});
    tick();
    const timer = setInterval(tick, 2000);
    return () => { stop = true; clearInterval(timer); };
  }, []);
  const liveOf = (signalId) => live.find((l) => l.signal_id === signalId);
  const liveJunctions = [...new Set(live.map((l) => l.junction_id))]
    .map((id) => ({ id, lights: live.filter((l) => l.junction_id === id) }))
    .sort((a, b) => a.id - b.id);

  const roadName = (id) => roads.find((r) => r.id === id)?.road_name || `Road ${id}`;
  const junctionName = (id) => junctions.find((j) => j.id === id)?.junction_name || `Junction ${id}`;
  const signalOf = (id) => state.data?.signals.find((s) => s.id === id);
  const set = (key) => (e) => setForm((f) => ({ ...f, values: { ...f.values, [key]: e.target.value } }));

  async function adjust() {
    setMessage("");
    await run(async () => {
      const result = await api.trafficSignal();
      setMessage(`${result.message}. ${result.red_time_changes?.length || 0} red times were balanced at junctions. Updated timings are shown below.`);
      return loadSignals();
    });
  }

  function openAdd() {
    setError("");
    setMessage("");
    const firstRoad = roads[0];
    setForm({
      mode: "add",
      values: { ...NEW_SIGNAL, road_id: String(firstRoad?.id || ""), junction_id: String(firstRoad?.to_junction_id || junctions[0]?.id || "") },
    });
  }
  function openEdit(timing) {
    setError("");
    setMessage("");
    setForm({ mode: "edit", timing, values: { green_time: timing.green_time, yellow_time: timing.yellow_time, red_time: timing.red_time } });
  }

  async function save() {
    const v = form.values;
    setBusy(true);
    setError("");
    try {
      const times = { green_time: Number(v.green_time), yellow_time: Number(v.yellow_time), red_time: Number(v.red_time) };
      if (form.mode === "add") {
        // 1. the signal (which road it controls, at which junction)  2. its all-day timing
        const signal = await api.createSignal({ junction_id: Number(v.junction_id), road_id: Number(v.road_id), current_state: "red" });
        await api.createTiming({ signal_id: signal.id, start_time: "00:00:00", end_time: "23:59:59", ...times });
        setMessage(`Signal #${signal.id} added with its timing.`);
      } else {
        const t = form.timing;
        await api.updateTiming(t.id, { signal_id: t.signal_id, start_time: t.start_time, end_time: t.end_time, ...times });
        setMessage(`Timing for signal #${t.signal_id} updated.`);
      }
      setForm(null);
      await run(loadSignals);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function remove(timing) {
    setMessage("");
    await run(async () => {
      await api.deleteTiming(timing.id);
      setMessage(`Timing row ${timing.id} deleted.`);
      return loadSignals();
    });
  }

  // When a road is picked, suggest the junction at its end (where the signal stands)
  function pickRoad(e) {
    const road = roads.find((r) => r.id === Number(e.target.value));
    setForm((f) => ({ ...f, values: { ...f.values, road_id: e.target.value, junction_id: String(road?.to_junction_id || f.values.junction_id) } }));
  }

  return (
    <>
      <PageHead
        eyebrow="Agent · Traffic Signal"
        title="Signal control"
        text="Each signal controls one road at a junction. The agent reads that road's live congestion and sets the green time by itself."
      >
        <div className="actions">
          {editable && !form && <button className="ghost" onClick={openAdd}>+ Add signal</button>}
          <button onClick={adjust} disabled={state.busy}>{state.busy ? "Adjusting..." : "Run signal agent"}</button>
        </div>
      </PageHead>

      <div className="tiles three">
        <div className="tile"><span className="badge low">low</span><b>30 s</b><small>green time</small></div>
        <div className="tile"><span className="badge medium">medium</span><b>45 s</b><small>green time</small></div>
        <div className="tile"><span className="badge high">high</span><b>60 s</b><small>green time</small></div>
      </div>

      {liveJunctions.length > 0 && (
        <div className="panel">
          <div className="panel-title">Live junctions <small className="muted">· updates every 2 s · 🚑 = held green for an emergency trip</small></div>
          <div className="junction-grid">
            {liveJunctions.map((j) => (
              <div key={j.id} className={`jcard ${j.lights.some((l) => l.mode === "emergency") ? "emergency" : ""}`}>
                <b>{junctionName(j.id)}</b>
                {j.lights.map((l) => (
                  <div key={l.signal_id} className="jrow">
                    <span className={`lamp ${l.state}`} />
                    <span className="jroad">{roadName(l.road_id).replace(/ to .*/, "")}</span>
                    <small>{l.mode === "emergency" ? (l.state === "green" ? "🚑" : "hold") : `${l.seconds_left}s`}</small>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}

      {form && (
        <FormPanel
          title={form.mode === "add" ? "Add a signal" : `Edit timing for signal #${form.timing.signal_id}`}
          onSubmit={save}
          onCancel={() => setForm(null)}
          busy={busy}
          error={error}
        >
          {form.mode === "add" && (
            <>
              <Field label="Road it controls" wide>
                <select value={form.values.road_id} onChange={pickRoad}>
                  {roads.map((r) => <option key={r.id} value={r.id}>{r.road_name}</option>)}
                </select>
              </Field>
              <Field label="At junction">
                <select value={form.values.junction_id} onChange={set("junction_id")}>
                  {junctions.map((j) => <option key={j.id} value={j.id}>{j.junction_name}</option>)}
                </select>
              </Field>
            </>
          )}
          <Field label="Green (s)"><input type="number" min="5" max="180" value={form.values.green_time} onChange={set("green_time")} required /></Field>
          <Field label="Yellow (s)"><input type="number" min="2" max="10" value={form.values.yellow_time} onChange={set("yellow_time")} required /></Field>
          <Field label="Red (s)"><input type="number" min="5" max="180" value={form.values.red_time} onChange={set("red_time")} required /></Field>
        </FormPanel>
      )}

      <div className="panel">
        {message && <div className="alert ok">{message}</div>}
        {state.error && <div className="alert error">{state.error}</div>}
        {!editable && <ViewOnlyNote />}
        {state.data && (
          state.data.timings.length === 0 ? (
            <p className="muted">No signals yet. {editable ? "Use “+ Add signal” above." : ""}</p>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr><th>Signal</th><th>Light now</th><th>Road</th><th>Junction</th><th>Green</th><th>Yellow</th><th>Red</th><th>Last updated</th>{editable && <th></th>}</tr>
                </thead>
                <tbody>
                  {state.data.timings.map((t) => {
                    const s = signalOf(t.signal_id);
                    return (
                      <tr key={t.id}>
                        <td>#{t.signal_id}</td>
                        <td>{(() => { const l = liveOf(t.signal_id); const st = l?.state || s?.current_state; return st && <span className={`badge ${LIGHT[st] || "none"}`}>{st}{l?.mode === "emergency" ? " 🚑" : ""}</span>; })()}</td>
                        <td>{s ? roadName(s.road_id) : "-"}</td>
                        <td>{s ? junctionName(s.junction_id) : "-"}</td>
                        <td><b className="green">{t.green_time}s</b></td>
                        <td>{t.yellow_time}s</td>
                        <td>{t.red_time}s</td>
                        <td className="muted">{t.updated_at.replace("T", " ").slice(0, 16)}</td>
                        {editable && (
                          <td>
                            <div className="row-actions">
                              <button className="small-btn ghost" onClick={() => openEdit(t)}>Edit</button>
                              <button className="small-btn ghost danger" onClick={() => remove(t)}>Delete</button>
                            </div>
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )
        )}
      </div>
    </>
  );
}
