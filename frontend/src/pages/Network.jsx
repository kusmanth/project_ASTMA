import { useEffect, useState } from "react";
import { api } from "../api.js";
import PageHead from "../components/PageHead.jsx";

const TABS = ["Roads", "Junctions", "Vehicles", "Hospitals", "Police stations"];

export default function Network({ junctions, roads }) {
  const [tab, setTab] = useState("Roads");
  const [extra, setExtra] = useState({ vehicles: [], hospitals: [], police: [] });

  useEffect(() => {
    const safe = (p) => p.catch(() => []);
    Promise.all([safe(api.vehicles()), safe(api.hospitals()), safe(api.policeStations())])
      .then(([vehicles, hospitals, police]) => setExtra({ vehicles, hospitals, police }));
  }, []);

  const junction = (id) => junctions.find((j) => j.id === id)?.junction_name || `Junction ${id}`;
  const active = (on) => <span className={`badge ${on ? "low" : "none"}`}>{on ? "active" : "inactive"}</span>;

  return (
    <>
      <PageHead
        eyebrow="Master data"
        title="City network"
        text="The roads, junctions, vehicles and services the agents work with. Roads are one-way."
      />
      <div className="tiles">
        <div className="tile"><small>Roads</small><b>{roads.length}</b></div>
        <div className="tile"><small>Junctions</small><b>{junctions.length}</b></div>
        <div className="tile"><small>Emergency vehicles</small><b>{extra.vehicles.length}</b></div>
        <div className="tile"><small>Hospitals</small><b>{extra.hospitals.length}</b></div>
        <div className="tile"><small>Police stations</small><b>{extra.police.length}</b></div>
      </div>

      <div className="panel">
        <div className="tabs">
          {TABS.map((t) => <button key={t} className={`tab ${tab === t ? "on" : ""}`} onClick={() => setTab(t)}>{t}</button>)}
        </div>
        <div className="table-wrap">
          <table className="table">
            {tab === "Roads" && (
              <>
                <thead><tr><th>#</th><th>Road</th><th>Direction</th><th>Distance</th><th>Lanes</th><th>Status</th></tr></thead>
                <tbody>{roads.map((r) => (
                  <tr key={r.id}><td>{r.id}</td><td>{r.road_name}</td>
                    <td>{junction(r.from_junction_id)} → {junction(r.to_junction_id)}</td>
                    <td>{r.distance_km} km</td><td>{r.lanes}</td><td>{active(r.is_active)}</td></tr>
                ))}</tbody>
              </>
            )}
            {tab === "Junctions" && (
              <>
                <thead><tr><th>#</th><th>Junction</th><th>Type</th><th>Status</th></tr></thead>
                <tbody>{junctions.map((j) => (
                  <tr key={j.id}><td>{j.id}</td><td>{j.junction_name}</td><td>{j.junction_type}-way</td><td>{active(j.is_active)}</td></tr>
                ))}</tbody>
              </>
            )}
            {tab === "Vehicles" && (
              <>
                <thead><tr><th>#</th><th>Number</th><th>Type</th><th>Priority</th><th>Status</th></tr></thead>
                <tbody>{extra.vehicles.map((v) => (
                  <tr key={v.id}><td>{v.id}</td><td><b>{v.vehicle_number}</b></td><td>{v.vehicle_type.replace("_", " ")}</td>
                    <td>{v.priority_level} / 5</td><td>{active(v.is_active)}</td></tr>
                ))}</tbody>
              </>
            )}
            {tab === "Hospitals" && (
              <>
                <thead><tr><th>#</th><th>Hospital</th><th>Nearest junction</th><th>Emergency</th><th>Status</th></tr></thead>
                <tbody>{extra.hospitals.map((h) => (
                  <tr key={h.id}><td>{h.id}</td><td>{h.hospital_name}</td><td>{junction(h.nearest_junction_id)}</td>
                    <td>{h.emergency_available ? "Yes" : "No"}</td><td>{active(h.is_active)}</td></tr>
                ))}</tbody>
              </>
            )}
            {tab === "Police stations" && (
              <>
                <thead><tr><th>#</th><th>Station</th><th>Nearest junction</th><th>Contact</th><th>Status</th></tr></thead>
                <tbody>{extra.police.map((p) => (
                  <tr key={p.id}><td>{p.id}</td><td>{p.station_name}</td><td>{junction(p.nearest_junction_id)}</td>
                    <td>{p.contact_number}</td><td>{active(p.is_active)}</td></tr>
                ))}</tbody>
              </>
            )}
          </table>
        </div>
      </div>
    </>
  );
}
