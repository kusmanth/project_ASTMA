import { useEffect, useState } from "react";
import { api, API_URL } from "./api.js";
import { Icon } from "./components/Icons.jsx";
import Overview from "./pages/Overview.jsx";
import Assistant from "./pages/Assistant.jsx";
import Monitoring from "./pages/Monitoring.jsx";
import Signals from "./pages/Signals.jsx";
import RoutePlanner from "./pages/RoutePlanner.jsx";
import Trips from "./pages/Trips.jsx";
import Network from "./pages/Network.jsx";
import Login from "./pages/Login.jsx";

const PAGES = [
  { id: "overview", label: "Overview", icon: Icon.home },
  { id: "assistant", label: "AI Assistant", icon: Icon.spark, ai: true },
  { id: "trips", label: "Emergency Trips", icon: Icon.siren },
  { id: "monitoring", label: "Traffic Monitoring", icon: Icon.gauge },
  { id: "signals", label: "Signal Control", icon: Icon.light },
  { id: "route", label: "Route Planner", icon: Icon.route },
  { id: "network", label: "City Network", icon: Icon.map },
];

// Remember the signed-in user in this browser (cleared on sign out)
function savedUser() {
  try {
    return JSON.parse(localStorage.getItem("astma_user")) || null;
  } catch {
    return null;
  }
}

export default function App() {
  const [user, setUser] = useState(savedUser);
  const [page, setPage] = useState("overview");
  const [online, setOnline] = useState(null);
  const [junctions, setJunctions] = useState([]);
  const [roads, setRoads] = useState([]);
  const [chat, setChat] = useState([]); // kept here so the chat survives page switches

  // Load junctions and roads once, and check that the API is running
  useEffect(() => {
    Promise.all([api.junctions(), api.roads()])
      .then(([j, r]) => {
        setJunctions(j);
        setRoads(r);
        setOnline(true);
      })
      .catch(() => setOnline(false));
  }, []);

  function login(u) {
    try { localStorage.setItem("astma_user", JSON.stringify(u)); } catch { /* private mode */ }
    setUser(u);
    setPage("overview");
  }
  function logout() {
    try { localStorage.removeItem("astma_user"); } catch { /* private mode */ }
    setUser(null);
    setChat([]);
  }

  if (!user) return <Login onLogin={login} />;

  const shared = { user, userId: user.id, junctions, roads, go: setPage };
  const initials = user.name.split(" ").map((w) => w[0]).join("").slice(0, 2).toUpperCase();

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo"><span /><span /><span /></div>
          <div>
            <b>ASTMA</b>
            <small>Smart traffic, calmer roads</small>
          </div>
        </div>

        <p className="nav-title">Workspace</p>
        <nav>
          {PAGES.map((p) => (
            <button
              key={p.id}
              className={`nav-item ${page === p.id ? "active" : ""}`}
              onClick={() => setPage(p.id)}
            >
              {p.icon}
              <span>{p.label}</span>
              {p.ai && <em>AI</em>}
            </button>
          ))}
        </nav>

        <div className="sidebar-foot">
          <div className="me">
            <div className="avatar">{initials}</div>
            <div>
              <b>{user.name}</b>
              <small><span className="role">{user.user_type.replace("_", " ")}</span> · id {user.id}</small>
            </div>
            <button className="ghost icon-btn" title="Sign out" onClick={logout}>{Icon.logout}</button>
          </div>
          <div className={`conn ${online ? "ok" : online === false ? "bad" : ""}`}>
            <i /> {online === null ? "Connecting..." : online ? "Connected to API" : "API offline"}
          </div>
        </div>
      </aside>

      <main className="content">
        {online === false && (
          <div className="alert error">
            Cannot reach the API at {API_URL}. Start it with <code>uv run uvicorn app.main:app --reload</code> and refresh.
          </div>
        )}
        {page === "overview" && <Overview {...shared} />}
        {page === "assistant" && <Assistant {...shared} chat={chat} setChat={setChat} />}
        {page === "monitoring" && <Monitoring />}
        {page === "signals" && <Signals roads={roads} />}
        {page === "route" && <RoutePlanner {...shared} />}
        {page === "trips" && <Trips {...shared} />}
        {page === "network" && <Network {...shared} />}
        <footer className="foot">ASTMA · AI Smart Traffic Management Agent</footer>
      </main>
    </div>
  );
}
