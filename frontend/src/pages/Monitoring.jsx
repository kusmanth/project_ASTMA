import { useEffect } from "react";
import { api } from "../api.js";
import PageHead from "../components/PageHead.jsx";
import useAction from "../components/useAction.js";
import { TrafficTable } from "../components/ResultView.jsx";

export default function Monitoring() {
  const [state, run] = useAction();
  useEffect(() => { run(api.trafficMonitoring); }, []);

  return (
    <>
      <PageHead
        eyebrow="Agent · Traffic Monitoring"
        title="Live traffic"
        text="Uses each road's latest available reading and rates the congestion."
      >
        <button onClick={() => run(api.trafficMonitoring)} disabled={state.busy}>
          {state.busy ? "Checking..." : "Check again"}
        </button>
      </PageHead>

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
