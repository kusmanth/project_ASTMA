import { useEffect, useState } from "react";
import { api } from "../api.js";
import { Icon } from "../components/Icons.jsx";
import PageHead from "../components/PageHead.jsx";

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
}

export default function Overview({ user, junctions, roads, go }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    // Each call is allowed to fail on its own, so one missing table never breaks the page
    const safe = (p) => p.catch(() => null);
    Promise.all([safe(api.signals()), safe(api.trips()), safe(api.routeRequests()), safe(api.trafficMonitoring())])
      .then(([signals, trips, routes, traffic]) => setStats({ signals, trips, routes, traffic: traffic?.results }));
  }, []);

  const count = (list) => (list ? list.length : "-");
  const activeTrips = stats?.trips ? stats.trips.filter((t) => t.status === "active").length : "-";
  const level = (name) => (stats?.traffic ? stats.traffic.filter((r) => r.traffic_status === name).length : "-");

  return (
    <>
      <PageHead
        eyebrow={`${greeting()}, ${user.name.split(" ")[0]}`}
        title="Traffic overview"
        text="A quick look at the city network and what the agents are seeing right now."
      />

      <div className="tiles">
        <button className="tile link" onClick={() => go("network")}><small>Junctions</small><b>{junctions.length}</b></button>
        <button className="tile link" onClick={() => go("network")}><small>Roads</small><b>{roads.length}</b></button>
        <div className="tile"><small>Signals</small><b>{count(stats?.signals)}</b></div>
        <button className="tile link" onClick={() => go("trips")}><small>Active emergency trips</small><b>{activeTrips}</b></button>
        <div className="tile"><small>Route requests</small><b>{count(stats?.routes)}</b></div>
      </div>

      <div className="split">
        <div className="panel">
          <h3>Traffic right now</h3>
          <div className="levels">
            <div><span className="badge high">high</span><b>{level("high")}</b><small>roads</small></div>
            <div><span className="badge medium">medium</span><b>{level("medium")}</b><small>roads</small></div>
            <div><span className="badge low">low</span><b>{level("low")}</b><small>roads</small></div>
            <div><span className="badge none">no data</span><b>{level("No recent data")}</b><small>roads</small></div>
          </div>
          <button className="ghost" onClick={() => go("monitoring")}>See all roads →</button>
        </div>

        <div className="panel">
          <h3>How the AI assistant works</h3>
          <ol className="flow">
            <li><b>Ask</b><span>Type a request in plain English.</span></li>
            <li><b>Plan</b><span>The orchestrator finds the right task in the knowledge base (Pinecone) and Gemini writes a plan.</span></li>
            <li><b>Approve</b><span>You check the plan. Nothing changes before this.</span></li>
            <li><b>Act</b><span>The right agent does the work and saves it in the database.</span></li>
          </ol>
          <button onClick={() => go("assistant")}>{Icon.spark} Open AI Assistant</button>
        </div>
      </div>

      <h3 className="section-title">Agents</h3>
      <div className="agent-cards">
        <button className="agent-card" onClick={() => go("assistant")}>
          {Icon.spark}<b>Orchestrator + Executor</b><span>Understands requests and books or ends emergency trips through MCP tools.</span>
        </button>
        <button className="agent-card" onClick={() => go("monitoring")}>
          {Icon.gauge}<b>Traffic Monitoring</b><span>Rates every road low, medium or high from live readings.</span>
        </button>
        <button className="agent-card" onClick={() => go("signals")}>
          {Icon.light}<b>Traffic Signal</b><span>Sets green time to 30, 45 or 60 seconds based on congestion.</span>
        </button>
        <button className="agent-card" onClick={() => go("route")}>
          {Icon.route}<b>Route Optimization</b><span>Finds the shortest path over one-way roads with Dijkstra.</span>
        </button>
      </div>
    </>
  );
}
