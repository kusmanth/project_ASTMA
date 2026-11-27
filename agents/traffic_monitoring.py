
"""Traffic Monitoring Agent: checks active roads and classifies congestion."""

from agents.mcp_server import list_roads, get_traffic_readings


def calculate_density(reading: dict, lanes: int) -> float:
    """Calculate weighted vehicle density per lane."""

    weighted_count = (
        reading["two_wheeler_count"] * 0.5
        + reading["three_wheeler_count"]
        + reading["four_wheeler_count"]
        + reading["heavy_vehicle_count"] * 3
    )

    return weighted_count / lanes


def classify_traffic(density: float) -> str:
    """Classify traffic based on density."""

    if density < 10:
        return "low"
    elif density <= 20:
        return "medium"
    else:
        return "high"


def monitor_traffic() -> list:
    """Monitor all active roads using their latest saved readings."""

    roads_result = list_roads()
    readings_result = get_traffic_readings()

    if roads_result["status_code"] != 200:
        raise RuntimeError("Could not retrieve roads from API.")

    if readings_result["status_code"] != 200:
        raise RuntimeError("Could not retrieve traffic readings from API.")

    roads = roads_result["data"] or []
    readings = readings_result["data"] or []

    reports = []

    for road in roads:

        if not road["is_active"]:
            continue

        road_readings = [
            reading for reading in readings
            if reading["road_id"] == road["id"]
        ]

        if not road_readings:
            reports.append({
                "road_id": road["id"],
                "road_name": road["road_name"],
                "lanes": road["lanes"],
                "density": None,
                "traffic_status": "No data"
            })
            continue

        latest_reading = max(
            road_readings,
            key=lambda item: item["reading_time"]
        )

        density = calculate_density(latest_reading, road["lanes"])
        congestion = classify_traffic(density)

        reports.append({
            "road_id": road["id"],
            "road_name": road["road_name"],
            "lanes": road["lanes"],
            "density": round(density, 2),
            "traffic_status": congestion
        })

    return reports


if __name__ == "__main__":
    print("\n===== TRAFFIC MONITORING AGENT =====")

    try:
        results = monitor_traffic()

        for result in results:
            print("\n", result)

    except Exception as error:
        print("Error:", error)

