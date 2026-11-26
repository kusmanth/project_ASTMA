"""Start fresh: ERASE all data, then build the clean ASTMA demo map.

What it does:
  1. Empties every table (users, junctions, roads, signals, readings, trips ...).
     The tables themselves stay, and ids start again from 1.
  2. Adds the demo map through our own APIs:
     9 junctions, 12 divided roads (= 24 one-way roads), 1 signal + timing per road,
     4 hospitals, 4 police stations, 5 vehicles, 3 demo users, fresh traffic readings.

The FastAPI server must be running. Run from the project folder:
    uv run python agents/scripts/reset_demo.py
"""
import random
import sys
from pathlib import Path

import httpx
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # project folder, so 'app' can be imported
from app.database import engine  # noqa: E402

API = "http://127.0.0.1:8000"

# name: (type = number of roads meeting, street, pincode, latitude, longitude)
JUNCTIONS = {
    "Madhapur Junction": (3, "Hitech City Road", "500081", 17.4483, 78.3915),
    "Jubilee Hills Checkpost": (4, "Road No. 36", "500033", 17.4300, 78.4100),
    "Ameerpet Junction": (4, "Ameerpet Main Road", "500016", 17.4375, 78.4482),
    "Punjagutta Circle": (4, "Punjagutta Road", "500082", 17.4262, 78.4510),
    "Begumpet Junction": (4, "Begumpet Road", "500016", 17.4447, 78.4664),
    "Khairatabad Junction": (4, "Raj Bhavan Road", "500004", 17.4100, 78.4600),
    "Lakdikapul Junction": (3, "Lakdikapul Road", "500004", 17.4040, 78.4650),
    "Paradise Circle": (4, "SP Road", "500003", 17.4434, 78.4867),
    "Secunderabad Junction": (4, "Station Road", "500003", 17.4399, 78.4983),
}

# Divided roads: (junction A, junction B, km, lanes per side).
# Each one becomes TWO one-way roads: A -> B and B -> A.
ROADS = [
    ("Madhapur Junction", "Jubilee Hills Checkpost", 4.0, 4),
    ("Jubilee Hills Checkpost", "Punjagutta Circle", 3.5, 4),
    ("Jubilee Hills Checkpost", "Ameerpet Junction", 4.0, 3),
    ("Ameerpet Junction", "Punjagutta Circle", 1.8, 4),
    ("Ameerpet Junction", "Begumpet Junction", 2.1, 3),
    ("Punjagutta Circle", "Khairatabad Junction", 1.8, 4),
    ("Khairatabad Junction", "Lakdikapul Junction", 1.2, 3),
    ("Punjagutta Circle", "Paradise Circle", 4.2, 6),
    ("Begumpet Junction", "Paradise Circle", 2.4, 4),
    ("Paradise Circle", "Secunderabad Junction", 1.5, 4),
    ("Begumpet Junction", "Secunderabad Junction", 3.0, 4),
    ("Khairatabad Junction", "Secunderabad Junction", 4.5, 4),
]

HOSPITALS = [
    ("City General Hospital", "Punjagutta Circle"),
    ("Metro Care Hospital", "Secunderabad Junction"),
    ("Lakeview Trauma Centre", "Khairatabad Junction"),
    ("Hitech Care Hospital", "Madhapur Junction"),
]
POLICE = [
    ("Ameerpet Traffic Police Station", "Ameerpet Junction", "9000000101"),
    ("Begumpet Police Station", "Begumpet Junction", "9000000102"),
    ("Secunderabad Traffic Police", "Secunderabad Junction", "9000000103"),
    ("Madhapur Police Station", "Madhapur Junction", "9000000104"),
]

USERS = [
    dict(name="Admin User", email="admin@astma.demo", mobile="9000000001", user_type="admin", password="admin12345"),
    dict(name="Police Officer", email="police@astma.demo", mobile="9000000002", user_type="police", password="police12345"),
    dict(name="Ravi Kumar", email="ravi@astma.demo", mobile="9876500001", user_type="emergency_driver", password="demo12345"),
]

# (number, type, priority, driver email or None, hospital or None)
# A hospital's ambulance always drives TO that hospital (any start point).
VEHICLES = [
    ("TS09AB1234", "ambulance", 5, "ravi@astma.demo", "City General Hospital"),
    ("AP09AB1234", "ambulance", 5, None, "Metro Care Hospital"),
    ("TS10FT0101", "fire_truck", 5, None, None),
    ("TS09PL7777", "police", 4, None, None),
    ("TS07VV0001", "vvip_convoy", 3, None, None),
]


def erase_everything() -> None:
    """Empty every table except alembic_version (the migration record)."""
    with engine.begin() as conn:
        tables = conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
        )).scalars().all()
        conn.execute(text(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE"))
    print(f"- erased {len(tables)} tables")


def main() -> None:
    answer = input("This ERASES all data in the database in .env (users too). Type YES to continue: ")
    if answer.strip() != "YES":
        raise SystemExit("Stopped. Nothing was changed.")

    with httpx.Client(base_url=API, timeout=30) as http:
        http.get("/junctions").raise_for_status()  # fail early if the API is not running

        def post(path, body):
            r = http.post(path, json=body)
            if r.status_code >= 400:
                raise SystemExit(f"POST {path} failed ({r.status_code}): {r.text}")
            return r.json()

        def new_address(street, pincode, lat, lng):
            return post("/address", dict(street=street, city="Hyderabad", state="Telangana",
                                         pincode=pincode, latitude=lat, longitude=lng))["id"]

        erase_everything()

        junctions = {}
        for name, (jtype, street, pin, lat, lng) in JUNCTIONS.items():
            junctions[name] = post("/junctions", dict(junction_name=name, junction_type=jtype,
                                                      address_id=new_address(street, pin, lat, lng)))["id"]
        print(f"+ {len(junctions)} junctions")

        roads = []
        for a, b, km, lanes in ROADS:
            for src, dst in ((a, b), (b, a)):
                roads.append(post("/roads", dict(road_name=f"{src.split()[0]} to {dst.split()[0]}",
                                                 from_junction_id=junctions[src], to_junction_id=junctions[dst],
                                                 distance_km=km, lanes=lanes)))
        print(f"+ {len(roads)} one-way roads ({len(ROADS)} divided roads)")

        # One signal per road, standing where the road enters its "to" junction
        for road in roads:
            signal = post("/signals", dict(junction_id=road["to_junction_id"], road_id=road["id"],
                                           current_state="red"))
            post("/signal-timings", dict(signal_id=signal["id"], start_time="00:00:00", end_time="23:59:59",
                                         green_time=45, yellow_time=5, red_time=60))
        print(f"+ {len(roads)} signals with all-day timings (all start red)")

        hospitals = {}
        for name, near in HOSPITALS:
            j = JUNCTIONS[near]
            hospitals[name] = post("/hospitals", dict(hospital_name=name, nearest_junction_id=junctions[near],
                                                      address_id=new_address(name, j[2], j[3], j[4])))["id"]
        for name, near, phone in POLICE:
            j = JUNCTIONS[near]
            post("/police-stations", dict(station_name=name, nearest_junction_id=junctions[near],
                                          contact_number=phone, address_id=new_address(name, j[2], j[3], j[4])))
        print(f"+ {len(HOSPITALS)} hospitals, {len(POLICE)} police stations")

        users = {u["email"]: post("/users", u)["id"] for u in USERS}
        for number, vtype, priority, driver, hospital in VEHICLES:
            post("/emergency-vehicles", dict(vehicle_number=number, vehicle_type=vtype, priority_level=priority,
                                             driver_id=users.get(driver), hospital_id=hospitals.get(hospital)))
        print(f"+ {len(USERS)} users, {len(VEHICLES)} vehicles")

        for road in roads:
            busy = random.choice([0.3, 1.0, 2.0])  # low, medium or high traffic
            half = road["lanes"] / 2
            counts = dict(two_wheeler_count=int(20 * busy * half), three_wheeler_count=int(6 * busy * half),
                          four_wheeler_count=int(14 * busy * half), heavy_vehicle_count=int(2 * busy * half))
            density = (counts["two_wheeler_count"] * 0.5 + counts["three_wheeler_count"]
                       + counts["four_wheeler_count"] + counts["heavy_vehicle_count"] * 3) / road["lanes"]
            level = "low" if density < 10 else "medium" if density <= 20 else "high"
            post("/traffic-readings", dict(road_id=road["id"], average_speed=round(45 / busy, 1),
                                           congestion_level=level, **counts))
        print(f"+ fresh traffic readings for {len(roads)} roads")

    print("\nDone. Log in with:")
    for u in USERS:
        print(f"  {u['user_type']:<17} {u['email']:<20} password: {u['password']}")


if __name__ == "__main__":
    main()
