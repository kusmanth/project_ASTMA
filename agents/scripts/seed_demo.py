"""Add demo data for the agent demo, through our own APIs.
The FastAPI server must be running. Run from the project folder:
uv run python -m scripts.seed_demo
"""
import httpx

API = "http://127.0.0.1:8000"

ADDRESSES = {
    "Ameerpet": dict(street="Ameerpet Main Road", landmark="Near Ameerpet Metro", city="Hyderabad",
                     state="Telangana", pincode="500016", latitude=17.4375, longitude=78.4482),
    "Punjagutta": dict(street="Punjagutta Road", landmark="Near Central Mall", city="Hyderabad",
                       state="Telangana", pincode="500082", latitude=17.4262, longitude=78.4510),
    "Begumpet": dict(street="Begumpet Road", landmark="Near Begumpet Airport", city="Hyderabad",
                     state="Telangana", pincode="500016", latitude=17.4447, longitude=78.4664),
    "Paradise": dict(street="SP Road", landmark="Opposite Paradise Hotel", city="Secunderabad",
                     state="Telangana", pincode="500003", latitude=17.4434, longitude=78.4867),
}

# junction name: (junction type, address key)
JUNCTIONS = {
    "Ameerpet Junction": (4, "Ameerpet"),
    "Punjagutta Circle": (4, "Punjagutta"),
    "Begumpet Junction": (3, "Begumpet"),
    "Paradise Circle": (5, "Paradise"),
}

# (road name, from junction, to junction, distance km, lanes) - all one-way
ROADS = [
    ("Ameerpet to Punjagutta", "Ameerpet Junction", "Punjagutta Circle", 1.6, 4),
    ("Punjagutta to Ameerpet", "Punjagutta Circle", "Ameerpet Junction", 1.6, 4),
    ("Ameerpet to Begumpet", "Ameerpet Junction", "Begumpet Junction", 2.1, 3),
    ("Begumpet to Paradise", "Begumpet Junction", "Paradise Circle", 2.4, 4),
    ("Paradise to Begumpet", "Paradise Circle", "Begumpet Junction", 2.4, 4),
    ("Punjagutta to Paradise", "Punjagutta Circle", "Paradise Circle", 4.2, 6),
]

VEHICLE = dict(vehicle_number="TS09AB1234", vehicle_type="ambulance", priority_level=1)
DRIVER = dict(name="Ravi Kumar", mobile="9876500001", email="ravi.demo@example.com",
              user_type="emergency_driver", password="demo12345")


def post(path: str, body: dict) -> dict:
    response = httpx.post(f"{API}{path}", json=body, follow_redirects=True)
    if response.status_code >= 400:
        raise SystemExit(f"POST {path} failed ({response.status_code}): {response.text}")
    return response.json()


def get(path: str) -> list:
    return httpx.get(f"{API}{path}", follow_redirects=True).json()


def main() -> None:
    if any(j["junction_name"] == "Ameerpet Junction" for j in get("/junctions")):
        print("Demo junctions already exist. Skipping junctions and roads.")
    else:
        address_ids = {key: post("/address", values)["id"] for key, values in ADDRESSES.items()}
        junction_ids = {}
        for name, (jtype, addr) in JUNCTIONS.items():
            junction_ids[name] = post("/junctions", dict(
                junction_name=name, junction_type=jtype, address_id=address_ids[addr]))["id"]
            print(f"Junction {junction_ids[name]}: {name}")
        for name, src, dst, km, lanes in ROADS:
            road = post("/roads", dict(road_name=name, from_junction_id=junction_ids[src],
                                       to_junction_id=junction_ids[dst], distance_km=km, lanes=lanes))
            print(f"Road {road['id']}: {name}")

    vehicle = next((v for v in get("/emergency-vehicles") if v["vehicle_number"] == VEHICLE["vehicle_number"]), None)
    if vehicle is None:
        vehicle = post("/emergency-vehicles", VEHICLE)
    print(f"Vehicle {vehicle['id']}: {vehicle['vehicle_number']}")

    driver = next((u for u in get("/users") if u["mobile"] == DRIVER["mobile"]), None)
    if driver is None:
        driver = post("/users", DRIVER)
    print(f"User {driver['id']}: {driver['name']} ({driver['user_type']})  <- use this id with --user")


if __name__ == "__main__":
    main()