import { useEffect, useState } from "react";
import { api } from "../api.js";
import PageHead from "../components/PageHead.jsx";
import useAction from "../components/useAction.js";

async function loadSignals() {
  const [signals, timings] = await Promise.all([api.signals(), api.signalTimings()]);
  return { signals, timings };
}

export default function Signals({ roads }) {
  const [state, run] = useAction();
  const [message, setMessage] = useState("");
  useEffect(() => { run(loadSignals); }, []);

  async function adjust() {
    setMessage("");
    await run(async () => {
      const result = await api.trafficSignal();
      setMessage(result.message);
      return loadSignals();
    });
  }

  const roadName = (id) => roads.find((r) => r.id === id)?.road_name || `Road ${id}`;
  const signalOf = (id) => state.data?.signals.find((s) => s.id === id);

  return (
    <>
      <PageHead
        eyebrow="Agent · Traffic Signal"
        title="Signal control"
        text="The agent reads live congestion and sets each signal's green time automatically."
      >
        <button onClick={adjust} disabled={state.busy}>{state.busy ? "Adjusting..." : "Run signal agent"}</button>
      </PageHead>

      <div className="tiles three">
        <div className="tile"><span className="badge low">low</span><b>30 s</b><small>green time</small></div>
        <div className="tile"><span className="badge medium">medium</span><b>45 s</b><small>green time</small></div>
        <div className="tile"><span className="badge high">high</span><b>60 s</b><small>green time</small></div>
      </div>

      <div className="panel">
        {message && <div className="alert ok">{message}. Updated timings are shown below.</div>}
        {state.error && <div className="alert error">{state.error}</div>}
        {state.data && (
          state.data.timings.length === 0 ? (
            <p className="muted">No signal timings yet. Add a signal and a timing in the API docs first.</p>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr><th>Signal</th><th>Road</th><th>Green</th><th>Yellow</th><th>Red</th><th>Last updated</th></tr>
                </thead>
                <tbody>
                  {state.data.timings.map((t) => (
                    <tr key={t.id}>
                      <td>#{t.signal_id}</td>
                      <td>{signalOf(t.signal_id) ? roadName(signalOf(t.signal_id).road_id) : "-"}</td>
                      <td><b className="green">{t.green_time}s</b></td>
                      <td>{t.yellow_time}s</td>
                      <td>{t.red_time}s</td>
                      <td className="muted">{t.updated_at.replace("T", " ").slice(0, 16)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}
      </div>
    </>
  );
}
