import { useEffect, useState } from "react";
import { api } from "../api.js";
import PageHead from "../components/PageHead.jsx";
import useAction from "../components/useAction.js";
import { RouteView } from "../components/ResultView.jsx";
import { reachableFrom } from "../components/reachable.js";

export default function RoutePlanner({ userId, junctions, roads }) {
  const [state, run] = useAction();
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  // "To" only offers junctions that roads actually connect to "From"
  const reachable = reachableFrom(from, roads);
  const destinations = junctions.filter((j) => reachable.has(j.id));

  // Pick the first junction by default once they load
  useEffect(() => {
    if (junctions.length && !from) setFrom(String(junctions[0].id));
  }, [junctions]);

  // When "From" changes, keep "To" only if it is still reachable
  useEffect(() => {
    if (!destinations.some((j) => String(j.id) === to))
      setTo(destinations.length ? String(destinations[destinations.length - 1].id) : "");
  }, [from, roads]);

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
          <button className="ghost swap" title="Swap" onClick={() => { if (to) { setFrom(to); setTo(from); } }}>⇄</button>
          <label>
            To
            <select value={to} onChange={(e) => setTo(e.target.value)}>
              {destinations.length === 0 && <option value="">No road leads out of here</option>}
              {destinations.map((j) => <option key={j.id} value={j.id}>{j.junction_name}</option>)}
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
