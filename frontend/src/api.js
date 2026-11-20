// All calls to the FastAPI backend live here.
export const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(method, path, body) {
  const response = await fetch(API_URL + path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    // FastAPI puts the error text in "detail"
    const detail = data?.detail;
    const message = typeof detail === "string" ? detail : JSON.stringify(detail || data);
    throw new Error(message || `Request failed (${response.status})`);
  }
  return data;
}

export const api = {
  // Agents
  plan: (text, userId) => request("POST", "/agents/plan", { request: text, user_id: userId }),
  execute: (plan, userId) => request("POST", "/agents/execute", { plan, user_id: userId }),
  trafficMonitoring: () => request("POST", "/agents/traffic-monitoring/run"),
  trafficSignal: () => request("POST", "/agents/traffic-signal/run"),
  routeOptimization: (userId, fromId, toId) =>
    request("POST", "/agents/route-optimization/run", {
      user_id: userId,
      from_junction_id: fromId,
      to_junction_id: toId,
    }),
  // Users
  login: (login, password) => request("POST", "/users/login", { login, password }),
  register: (user) => request("POST", "/users", user),
  // Emergency trips
  vehicles: () => request("GET", "/emergency-vehicles"),
  createTrip: (trip) => request("POST", "/emergency-trips", trip),
  setTripStatus: (id, status) => request("PATCH", `/emergency-trips/${id}`, { status }),
  // Data
  hospitals: () => request("GET", "/hospitals"),
  policeStations: () => request("GET", "/police-stations"),
  junctions: () => request("GET", "/junctions"),
  roads: () => request("GET", "/roads"),
  signals: () => request("GET", "/signals"),
  signalTimings: () => request("GET", "/signal-timings"),
  trips: () => request("GET", "/emergency-trips"),
  routeRequests: () => request("GET", "/route-requests"),
};
