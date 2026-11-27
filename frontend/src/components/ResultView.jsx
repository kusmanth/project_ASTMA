// Shows agent results in a friendly way instead of raw JSON.

export function StatusBadge({ status }) {
  const cls = ["low", "medium", "high"].includes(status) ? status : "none";
  return <span className={`badge ${cls}`}>{status}</span>;
}

export function TrafficTable({ reports }) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr><th>Road</th><th>Lanes</th><th>Density</th><th>Status</th></tr>
        </thead>
        <tbody>
          {reports.map((r) => (
            <tr key={r.road_id}>
              <td>{r.road_name}</td>
              <td>{r.lanes ?? "-"}</td>
              <td>{r.density ?? "-"}</td>
              <td><StatusBadge status={r.traffic_status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function RouteView({ result, roads, junctions }) {
  const road = (id) => roads.find((r) => r.id === id);
  const junctionName = (id) => junctions.find((j) => j.id === id)?.junction_name || `Junction ${id}`;
  const legs = result.suggested_route.map(road).filter(Boolean);
  const stops = legs.length ? [legs[0].from_junction_id, ...legs.map((l) => l.to_junction_id)] : [];

  return (
    <div className="route">
      <div className="route-total">
        <span>{result.total_distance_km} km</span>
        <small>{legs.length} road{legs.length === 1 ? "" : "s"} · shortest path</small>
      </div>
      <ol className="route-line">
        {stops.map((id, i) => (
          <li key={i}>
            <span className={`dot ${i === 0 ? "start" : i === stops.length - 1 ? "end" : ""}`} />
            <div>
              <b>{junctionName(id)}</b>
              {legs[i] && <small>via {legs[i].road_name} · {legs[i].distance_km} km</small>}
            </div>
          </li>
        ))}
      </ol>
      {result.reasons?.length > 0 && (
        <div className="why">
          <b>Why this route?</b>
          <ul>{result.reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
        </div>
      )}
      {result.route_request && <p className="muted small">Saved as route request #{result.route_request.id}</p>}
    </div>
  );
}

export default function ResultView({ data, roads, junctions }) {
  const { agent, result } = data;
  return (
    <div className="result">
      <div className="result-head">✓ Done by the <b>{agent.replace(/_/g, " ")}</b> agent</div>
      {agent === "traffic_monitoring" && <TrafficTable reports={result} />}
      {agent === "route_optimization" && <RouteView result={result} roads={roads} junctions={junctions} />}
      {agent === "executor" && <p className="answer">{result || "Done."}</p>}
    </div>
  );
}
