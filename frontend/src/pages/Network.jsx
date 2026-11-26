import { useEffect, useState } from "react";
import { api } from "../api.js";
import PageHead from "../components/PageHead.jsx";
import { Field, FormPanel, ViewOnlyNote, canEdit } from "../components/Form.jsx";

const TABS = ["Roads", "Junctions", "Vehicles", "Hospitals", "Police stations"];
const VEHICLE_TYPES = ["ambulance", "fire_truck", "police", "vvip_convoy"];

const EMPTY = {
  Roads: { road_name: "", from_junction_id: "", to_junction_id: "", distance_km: "", lanes: 2, two_way: true, is_active: true },
  Junctions: { junction_name: "", junction_type: 4, street: "", city: "Hyderabad", state: "Telangana", pincode: "500016", latitude: "17.43", longitude: "78.45", is_active: true },
  Vehicles: { vehicle_number: "", vehicle_type: "ambulance", priority_level: 5, driver_id: "", is_active: true },
};

export default function Network({ user, junctions, roads, reload }) {
  const [tab, setTab] = useState("Roads");
  const [extra, setExtra] = useState({ vehicles: [], hospitals: [], police: [], users: [] });
  const [form, setForm] = useState(null); // { mode: "add" | "edit", id, values }
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const editable = canEdit(user);

  async function loadExtra() {
    const safe = (p) => p.catch(() => []);
    const [vehicles, hospitals, police, users] = await Promise.all([
      safe(api.vehicles()), safe(api.hospitals()), safe(api.policeStations()), safe(api.users()),
    ]);
    setExtra({ vehicles, hospitals, police, users });
  }
  useEffect(() => { loadExtra(); }, []);

  const junction = (id) => junctions.find((j) => j.id === id)?.junction_name || `Junction ${id}`;
  const driverName = (id) => extra.users.find((u) => u.id === id)?.name || "-";
  const drivers = extra.users.filter((u) => u.user_type === "emergency_driver");
  const badge = (on) => <span className={`badge ${on ? "low" : "none"}`}>{on ? "active" : "inactive"}</span>;
  const set = (key) => (e) => {
    const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setForm((f) => ({ ...f, values: { ...f.values, [key]: value } }));
  };

  function openAdd() {
    setError("");
    setNotice("");
    const values = { ...EMPTY[tab] };
    if (tab === "Roads" && junctions.length >= 2) {
      values.from_junction_id = String(junctions[0].id);
      values.to_junction_id = String(junctions[1].id);
    }
    setForm({ mode: "add", values });
  }
  function openEdit(row) {
    setError("");
    setNotice("");
    const values = { ...EMPTY[tab], ...row };
    setForm({ mode: "edit", id: row.id, values });
  }

  async function save() {
    const v = form.values;
    setBusy(true);
    setError("");
    try {
      if (tab === "Roads") {
        const road = {
          road_name: v.road_name,
          from_junction_id: Number(v.from_junction_id),
          to_junction_id: Number(v.to_junction_id),
          distance_km: Number(v.distance_km),
          lanes: Number(v.lanes),
          is_active: v.is_active,
        };
        if (road.from_junction_id === road.to_junction_id) throw new Error("From and To must be different junctions.");
        if (form.mode === "edit") {
          await api.updateRoad(form.id, road);
          setNotice("Road updated.");
        } else {
          await api.createRoad(road);
          // Two-way: also add the road in the other direction
          if (v.two_way) {
            await api.createRoad({
              ...road,
              road_name: `${junction(road.to_junction_id)} to ${junction(road.from_junction_id)}`,
              from_junction_id: road.to_junction_id,
              to_junction_id: road.from_junction_id,
            });
          }
          setNotice(v.two_way ? "Road added in both directions." : "One-way road added.");
        }
      }
      if (tab === "Junctions") {
        if (form.mode === "edit") {
          await api.updateJunction(form.id, { junction_name: v.junction_name, junction_type: Number(v.junction_type), is_active: v.is_active });
          setNotice("Junction updated.");
        } else {
          const address = await api.createAddress({
            street: v.street || v.junction_name, city: v.city, state: v.state, pincode: v.pincode,
            latitude: Number(v.latitude), longitude: Number(v.longitude),
          });
          await api.createJunction({ junction_name: v.junction_name, junction_type: Number(v.junction_type), address_id: address.id, is_active: true });
          setNotice("Junction added.");
        }
      }
      if (tab === "Vehicles") {
        const vehicle = {
          vehicle_number: v.vehicle_number.toUpperCase().replace(/\s/g, ""),
          vehicle_type: v.vehicle_type,
          priority_level: Number(v.priority_level),
          driver_id: v.driver_id ? Number(v.driver_id) : null,
          is_active: v.is_active,
        };
        if (form.mode === "edit") await api.updateVehicle(form.id, vehicle);
        else await api.createVehicle(vehicle);
        setNotice(form.mode === "edit" ? "Vehicle updated." : "Vehicle added.");
      }
      setForm(null);
      await Promise.all([reload(), loadExtra()]);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function toggle(row) {
    setNotice("");
    try {
      if (tab === "Roads") await api.updateRoad(row.id, { is_active: !row.is_active });
      if (tab === "Junctions") await api.updateJunction(row.id, { is_active: !row.is_active });
      if (tab === "Vehicles") await api.updateVehicle(row.id, { is_active: !row.is_active });
      await Promise.all([reload(), loadExtra()]);
    } catch (err) {
      setError(err.message);
    }
  }

  const rowActions = (row) =>
    editable && (
      <td>
        <div className="row-actions">
          <button className="small-btn ghost" onClick={() => openEdit(row)}>Edit</button>
          <button className="small-btn ghost" onClick={() => toggle(row)}>{row.is_active ? "Deactivate" : "Activate"}</button>
        </div>
      </td>
    );
  const canAdd = editable && ["Roads", "Junctions", "Vehicles"].includes(tab);

  return (
    <>
      <PageHead
        eyebrow="Master data"
        title="City network"
        text="The roads, junctions, vehicles and services the agents work with. Each road row is one direction of travel."
      />
      <div className="tiles">
        <div className="tile"><small>Roads</small><b>{roads.length}</b></div>
        <div className="tile"><small>Junctions</small><b>{junctions.length}</b></div>
        <div className="tile"><small>Emergency vehicles</small><b>{extra.vehicles.length}</b></div>
        <div className="tile"><small>Hospitals</small><b>{extra.hospitals.length}</b></div>
        <div className="tile"><small>Police stations</small><b>{extra.police.length}</b></div>
      </div>

      {form && (
        <FormPanel
          title={`${form.mode === "add" ? "Add" : "Edit"} ${tab.slice(0, -1).toLowerCase()}`}
          onSubmit={save}
          onCancel={() => setForm(null)}
          busy={busy}
          error={error}
        >
          {tab === "Roads" && (
            <>
              <Field label="Road name" wide><input value={form.values.road_name} onChange={set("road_name")} minLength={4} required placeholder="Ameerpet to Begumpet" /></Field>
              <Field label="From junction">
                <select value={form.values.from_junction_id} onChange={set("from_junction_id")}>
                  {junctions.map((j) => <option key={j.id} value={j.id}>{j.junction_name}</option>)}
                </select>
              </Field>
              <Field label="To junction">
                <select value={form.values.to_junction_id} onChange={set("to_junction_id")}>
                  {junctions.map((j) => <option key={j.id} value={j.id}>{j.junction_name}</option>)}
                </select>
              </Field>
              <Field label="Distance (km)"><input type="number" step="0.1" min="0.1" value={form.values.distance_km} onChange={set("distance_km")} required /></Field>
              <Field label="Lanes"><input type="number" min="1" max="8" value={form.values.lanes} onChange={set("lanes")} required /></Field>
              {form.mode === "add" && (
                <label className="check wide">
                  <input type="checkbox" checked={form.values.two_way} onChange={set("two_way")} />
                  Two-way road (also add the return direction)
                </label>
              )}
            </>
          )}
          {tab === "Junctions" && (
            <>
              <Field label="Junction name" wide><input value={form.values.junction_name} onChange={set("junction_name")} minLength={4} required placeholder="Khairatabad Junction" /></Field>
              <Field label="Type">
                <select value={form.values.junction_type} onChange={set("junction_type")}>
                  {[2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}-way</option>)}
                </select>
              </Field>
              {form.mode === "add" && (
                <>
                  <Field label="Street / area"><input value={form.values.street} onChange={set("street")} placeholder="Raj Bhavan Road" /></Field>
                  <Field label="City"><input value={form.values.city} onChange={set("city")} required /></Field>
                  <Field label="State"><input value={form.values.state} onChange={set("state")} required /></Field>
                  <Field label="Pincode"><input value={form.values.pincode} onChange={set("pincode")} pattern="\d{6}" title="6 digits" required /></Field>
                  <Field label="Latitude"><input type="number" step="any" value={form.values.latitude} onChange={set("latitude")} required /></Field>
                  <Field label="Longitude"><input type="number" step="any" value={form.values.longitude} onChange={set("longitude")} required /></Field>
                </>
              )}
            </>
          )}
          {tab === "Vehicles" && (
            <>
              <Field label="Vehicle number"><input value={form.values.vehicle_number} onChange={set("vehicle_number")} minLength={4} required placeholder="TS09AB1234" /></Field>
              <Field label="Type">
                <select value={form.values.vehicle_type} onChange={set("vehicle_type")}>
                  {VEHICLE_TYPES.map((t) => <option key={t} value={t}>{t.replace("_", " ")}</option>)}
                </select>
              </Field>
              <Field label="Priority (1 to 5)"><input type="number" min="1" max="5" value={form.values.priority_level} onChange={set("priority_level")} required /></Field>
              <Field label="Driver">
                <select value={form.values.driver_id ?? ""} onChange={set("driver_id")}>
                  <option value="">No driver</option>
                  {drivers.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select>
              </Field>
            </>
          )}
        </FormPanel>
      )}

      {notice && <div className="alert ok">{notice}</div>}
      {error && !form && <div className="alert error">{error}</div>}

      <div className="panel">
        <div className="tabs-row">
          <div className="tabs">
            {TABS.map((t) => (
              <button key={t} className={`tab ${tab === t ? "on" : ""}`} onClick={() => { setTab(t); setForm(null); setNotice(""); }}>{t}</button>
            ))}
          </div>
          {canAdd && !form && <button onClick={openAdd}>+ Add {tab.slice(0, -1).toLowerCase()}</button>}
        </div>
        {!editable && <ViewOnlyNote />}

        <div className="table-wrap">
          <table className="table">
            {tab === "Roads" && (
              <>
                <thead><tr><th>#</th><th>Road</th><th>Direction</th><th>Distance</th><th>Lanes</th><th>Status</th>{editable && <th></th>}</tr></thead>
                <tbody>{roads.map((r) => (
                  <tr key={r.id}><td>{r.id}</td><td>{r.road_name}</td>
                    <td>{junction(r.from_junction_id)} → {junction(r.to_junction_id)}</td>
                    <td>{r.distance_km} km</td><td>{r.lanes}</td><td>{badge(r.is_active)}</td>{rowActions(r)}</tr>
                ))}</tbody>
              </>
            )}
            {tab === "Junctions" && (
              <>
                <thead><tr><th>#</th><th>Junction</th><th>Type</th><th>Status</th>{editable && <th></th>}</tr></thead>
                <tbody>{junctions.map((j) => (
                  <tr key={j.id}><td>{j.id}</td><td>{j.junction_name}</td><td>{j.junction_type}-way</td><td>{badge(j.is_active)}</td>{rowActions(j)}</tr>
                ))}</tbody>
              </>
            )}
            {tab === "Vehicles" && (
              <>
                <thead><tr><th>#</th><th>Number</th><th>Type</th><th>Priority</th><th>Driver</th><th>Status</th>{editable && <th></th>}</tr></thead>
                <tbody>{extra.vehicles.map((v) => (
                  <tr key={v.id}><td>{v.id}</td><td><b>{v.vehicle_number}</b></td><td>{v.vehicle_type.replace("_", " ")}</td>
                    <td>{v.priority_level} / 5</td><td>{driverName(v.driver_id)}</td><td>{badge(v.is_active)}</td>{rowActions(v)}</tr>
                ))}</tbody>
              </>
            )}
            {tab === "Hospitals" && (
              <>
                <thead><tr><th>#</th><th>Hospital</th><th>Nearest junction</th><th>Emergency</th><th>Status</th></tr></thead>
                <tbody>{extra.hospitals.map((h) => (
                  <tr key={h.id}><td>{h.id}</td><td>{h.hospital_name}</td><td>{junction(h.nearest_junction_id)}</td>
                    <td>{h.emergency_available ? "Yes" : "No"}</td><td>{badge(h.is_active)}</td></tr>
                ))}</tbody>
              </>
            )}
            {tab === "Police stations" && (
              <>
                <thead><tr><th>#</th><th>Station</th><th>Nearest junction</th><th>Contact</th><th>Status</th></tr></thead>
                <tbody>{extra.police.map((p) => (
                  <tr key={p.id}><td>{p.id}</td><td>{p.station_name}</td><td>{junction(p.nearest_junction_id)}</td>
                    <td>{p.contact_number}</td><td>{badge(p.is_active)}</td></tr>
                ))}</tbody>
              </>
            )}
          </table>
        </div>
      </div>
    </>
  );
}
