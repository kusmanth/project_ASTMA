import { useEffect, useState } from "react";
import { api } from "../api.js";
import PageHead from "../components/PageHead.jsx";
import useAction from "../components/useAction.js";
import { RouteView } from "../components/ResultView.jsx";

export default function RoutePlanner({ userId, junctions, roads }) {
  const [state, run] = useAction();
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  // Pick the first and last junction by default once they load
  useEffect(() => {
    if (junctions.length >= 2 && !from && !to) {
      setFrom(String(junctions[0].id));
      setTo(String(junctions[junctions.length - 1].id));
    }
  }, [junctions]);

  return (
    <>
      <PageHead
        eyebrow="Agent · Route Optimization"
        title="Route planner"
        text="Finds the shortest route between two junctions over one-way roads, using Dijkstra's algorithm."
      />

      <div className="panel">
        <div className="form-row">
          <label>
            From
            <select value={from} onChange={(e) => setFrom(e.target.value)}>
              {junctions.map((j) => <option key={j.id} value={j.id}>{j.junction_name}</option>)}
            </select>
          </label>
          <button className="ghost swap" title="Swap" onClick={() => { setFrom(to); setTo(from); }}>⇄</button>
          <label>
            To
            <select value={to} onChange={(e) => setTo(e.target.value)}>
              {junctions.map((j) => <option key={j.id} value={j.id}>{j.junction_name}</option>)}
            </select>
          </label>
          <button
            onClick={() => run(() => api.routeOptimization(userId, Number(from), Number(to)))}
            disabled={state.busy || !from || !to}
          >
            {state.busy ? "Finding..." : "Find route"}
          </button>
        </div>
        {state.error && <div className="alert error">{state.error}</div>}
      </div>

      {state.data && (
        <div className="panel">
          <RouteView result={state.data} roads={roads} junctions={junctions} />
        </div>
      )}
    </>
  );
}
