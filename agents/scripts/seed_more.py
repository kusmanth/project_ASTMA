"""Add more demo data on top of seed_demo.py, through our own APIs.

Safe to run more than once: anything that already exists (same name / number) is skipped.
The FastAPI server must be running. Run from the project folder:
    uv run python agents/scripts/seed_more.py
"""
import random

import httpx

API = "http://127.0.0.1:8000"
CITY = dict(city="Hyderabad", state="Telangana")

# New junctions: name -> (type, street, pincode, latitude, longitude)
JUNCTIONS = {
    "Khairatabad Junction": (4, "Raj Bhavan Road", "500004", 17.4100, 78.4600),
    "Lakdikapul Junction": (3, "Lakdikapul Road", "500004", 17.4040, 78.4650),
    "Secunderabad Junction": (4, "Station Road", "500003", 17.4399, 78.4983),
}

# Roads: (from, to, km, lanes). Each one is created in BOTH directions (two-way).
ROADS = [
    ("Ameerpet Junction", "Begumpet Junction", 2.1, 3),     # adds the missing Begumpet -> Ameerpet
    ("Punjagutta Circle", "Paradise Circle", 4.2, 6),       # adds the missing Paradise -> Punjagutta
    ("Punjagutta Circle", "Khairatabad Junction", 1.8, 4),
    ("Khairatabad Junction", "Lakdikapul Junction", 1.2, 3),
    ("Paradise Circle", "Secunderabad Junction", 1.5, 4),
    ("Begumpet Junction", "Secunderabad Junction", 3.0, 4),
]

VEHICLES = [
    dict(vehicle_number="TS09AB1234", vehicle_type="ambulance", priority_level=5),
    dict(vehicle_number="AP09AB1234", vehicle_type="ambulance", priority_level=5),
    dict(vehicle_number="TS10FT0101", vehicle_type="fire_truck", priority_level=5),
    dict(vehicle_number="TS09PL7777", vehicle_type="police", priority_level=4),
    dict(vehicle_number="TS07VV0001", vehicle_type="vvip_convoy", priority_level=3),
]

# (name, nearest junction)
HOSPITALS = [("City General Hospital", "Punjagutta Circle"), ("Metro Care Hospital", "Secunderabad Junction"),
             ("Lakeview Trauma Centre", "Khairatabad Junction")]
POLICE = [("Ameerpet Traffic Police Station", "Ameerpet Junction", "9000000101"),
          ("Begumpet Police Station", "Begumpet Junction", "9000000102"),
          ("Secunderabad Traffic Police", "Secunderabad Junction", "9000000103")]


def main() -> None:
    with httpx.Client(base_url=API, timeout=30) as http:
        def get(path):
            r = http.get(path)
            r.raise_for_status()
            return r.json()

        def post(path, body):
            r = http.post(path, json=body)
            if r.status_code >= 400:
                raise SystemExit(f"POST {path} failed ({r.status_code}): {r.text}")
            return r.json()

        def new_address(street, pincode, lat, lng):
            return post("/address", dict(street=street, pincode=pincode, latitude=lat, longitude=lng, **CITY))["id"]

        # 1. Junctions
        junctions = {j["junction_name"]: j["id"] for j in get("/junctions")}
        for name, (jtype, street, pin, lat, lng) in JUNCTIONS.items():
            if name not in junctions:
                junctions[name] = post("/junctions", dict(junction_name=name, junction_type=jtype,
                                                          address_id=new_address(street, pin, lat, lng)))["id"]
                print(f"+ junction {name}")

        # 2. Roads in both directions
        existing = {(r["from_junction_id"], r["to_junction_id"]) for r in get("/roads")}
        for a, b, km, lanes in ROADS:
            for src, dst in ((a, b), (b, a)):
                key = (junctions[src], junctions[dst])
                if key in existing:
                    continue
                name = f"{src.split()[0]} to {dst.split()[0]}"
                post("/roads", dict(road_name=name, from_junction_id=key[0], to_junction_id=key[1],
                                    distance_km=km, lanes=lanes))
                existing.add(key)
                print(f"+ road {name}")

        # 3. Vehicles
        numbers = {v["vehicle_number"] for v in get("/emergency-vehicles")}
        for v in VEHICLES:
            if v["vehicle_number"] not in numbers:
                post("/emergency-vehicles", v)
                print(f"+ vehicle {v['vehicle_number']}")

        # 4. Hospitals and police stations
        hospitals = {h["hospital_name"] for h in get("/hospitals")}
        for name, near in HOSPITALS:
            if name not in hospitals:
                post("/hospitals", dict(hospital_name=name, nearest_junction_id=junctions[near],
                                        address_id=new_address(name, "500004", 17.42, 78.46)))
                print(f"+ hospital {name}")
        stations = {p["station_name"] for p in get("/police-stations")}
        for name, near, phone in POLICE:
            if name not in stations:
                post("/police-stations", dict(station_name=name, nearest_junction_id=junctions[near],
                                              contact_number=phone,
                                              address_id=new_address(name, "500016", 17.44, 78.46)))
                print(f"+ police station {name}")

        # 5. One signal + all-day timing for every road that has none (signal stands at the road's end)
        roads = get("/roads")
        signalled = {s["road_id"] for s in get("/signals")}
        for road in roads:
            if road["id"] in signalled or not road["is_active"]:
                continue
            signal = post("/signals", dict(junction_id=road["to_junction_id"], road_id=road["id"], current_state="red"))
            post("/signal-timings", dict(signal_id=signal["id"], start_time="00:00:00", end_time="23:59:59",
                                         green_time=45, yellow_time=5, red_time=60))
            print(f"+ signal {signal['id']} on {road['road_name']}")

        # 6. Fresh traffic readings (valid for 15 minutes) so the dashboard shows low / medium / high
        for road in roads:
            if not road["is_active"]:
                continue
            busy = random.choice([0.3, 1.0, 2.0])  # low, medium or high traffic
            counts = dict(two_wheeler_count=int(20 * busy * road["lanes"] / 2),
                          three_wheeler_count=int(6 * busy * road["lanes"] / 2),
                          four_wheeler_count=int(14 * busy * road["lanes"] / 2),
                          heavy_vehicle_count=int(2 * busy * road["lanes"] / 2))
            density = (counts["two_wheeler_count"] * 0.5 + counts["three_wheeler_count"]
                       + counts["four_wheeler_count"] + counts["heavy_vehicle_count"] * 3) / road["lanes"]
            level = "low" if density < 10 else "medium" if density <= 20 else "high"
            post("/traffic-readings", dict(road_id=road["id"], average_speed=round(45 / busy, 1),
                                           congestion_level=level, **counts))
        print(f"+ fresh traffic readings for {len(roads)} roads")
        print("Done.")


if __name__ == "__main__":
    main()
