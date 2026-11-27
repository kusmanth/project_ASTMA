
"""Route Optimization Agent: finds the shortest available route."""

import heapq

from agents.mcp_server import (
    get_user,
    get_junctions,
    list_roads,
    create_route_request,
)


def find_shortest_route(
    from_junction_id: int,
    to_junction_id: int,
    roads: list,
    junctions: list
) -> dict:
    """Find the shortest route using Dijkstra's algorithm."""

    active_junctions = {
        junction["id"]
        for junction in junctions
        if junction["is_active"]
    }

    if from_junction_id not in active_junctions:
        raise ValueError("Starting junction is not active or does not exist.")

    if to_junction_id not in active_junctions:
        raise ValueError("Destination junction is not active or does not exist.")

    if from_junction_id == to_junction_id:
        raise ValueError("Starting and destination junctions must be different.")

    graph = {junction_id: [] for junction_id in active_junctions}

    for road in roads:
        if not road["is_active"]:
            continue

        start = road["from_junction_id"]
        end = road["to_junction_id"]

        if start not in active_junctions or end not in active_junctions:
            continue

        distance = road["distance_km"]

        graph[start].append((end, distance, road["id"]))  # roads are one-way
    
    distances = {junction_id: float("inf") for junction_id in active_junctions}
    previous = {}

    distances[from_junction_id] = 0
    queue = [(0, from_junction_id)]

    while queue:
        current_distance, current_junction = heapq.heappop(queue)

        if current_distance > distances[current_junction]:
            continue

        if current_junction == to_junction_id:
            break

        for next_junction, road_distance, road_id in graph[current_junction]:
            new_distance = current_distance + road_distance

            if new_distance < distances[next_junction]:
                distances[next_junction] = new_distance
                previous[next_junction] = (current_junction, road_id)

                heapq.heappush(
                    queue,
                    (new_distance, next_junction)
                )

    if distances[to_junction_id] == float("inf"):
        raise ValueError("No available route found between these junctions.")

    route = []
    current = to_junction_id

    while current != from_junction_id:
        previous_junction, road_id = previous[current]
        route.append(road_id)
        current = previous_junction

    route.reverse()

    return {
        "suggested_route": route,
        "total_distance_km": round(distances[to_junction_id], 2)
    }


def explain_route(from_junction_id: int, to_junction_id: int, chosen: dict,
                  roads: list, junctions: list) -> list[str]:
    """Say in plain words why this route was chosen."""

    names = {j["id"]: j.get("junction_name", f"Junction {j['id']}") for j in junctions}
    by_id = {r["id"]: r for r in roads}

    def path(route_ids):
        stops = [names[by_id[route_ids[0]]["from_junction_id"]]]
        stops += [names[by_id[r]["to_junction_id"]] for r in route_ids]
        return " → ".join(stops)

    reasons = [f"Shortest open route: {chosen['total_distance_km']} km over "
               f"{len(chosen['suggested_route'])} roads ({path(chosen['suggested_route'])})."]

    # What would the best route be if every road and junction were open?
    all_open = find_shortest_route(
        from_junction_id, to_junction_id,
        [{**r, "is_active": True} for r in roads],
        [{**j, "is_active": True} for j in junctions],
    )
    if all_open["total_distance_km"] < chosen["total_distance_km"]:
        closed = [f"road '{by_id[r].get('road_name', r)}' is closed"
                  for r in all_open["suggested_route"] if not by_id[r]["is_active"]]
        closed += [f"junction {names[by_id[r]['to_junction_id']]} is closed"
                   for r in all_open["suggested_route"][:-1]
                   if not next(j for j in junctions if j["id"] == by_id[r]["to_junction_id"])["is_active"]]
        reasons.append(f"A shorter route ({all_open['total_distance_km']} km, {path(all_open['suggested_route'])}) "
                       f"was skipped because {' and '.join(closed)}.")
    else:
        reasons.append("No closed roads or junctions affect this trip; this is the shortest route on the map.")
    return reasons


def optimize_route(
    user_id: int,
    from_junction_id: int,
    to_junction_id: int
) -> dict:
    """Find and save the shortest available route."""

    user_result = get_user(user_id)

    if user_result["status_code"] != 200:
        raise ValueError("User not found.")

    junction_result = get_junctions()
    roads_result = list_roads()

    if junction_result["status_code"] != 200:
        raise RuntimeError("Could not retrieve junctions.")

    if roads_result["status_code"] != 200:
        raise RuntimeError("Could not retrieve roads.")

    junctions = junction_result["data"] or []
    roads = roads_result["data"] or []

    route_result = find_shortest_route(
        from_junction_id,
        to_junction_id,
        roads,
        junctions
    )

    save_result = create_route_request(
        user_id=user_id,
        from_junction_id=from_junction_id,
        to_junction_id=to_junction_id,
        suggested_route=route_result["suggested_route"]
    )

    if save_result["status_code"] not in [200, 201]:
        raise RuntimeError(f"Could not save route: {save_result['data']}")

    return {
        "message": "Route optimized and saved successfully.",
        "user_id": user_id,
        "from_junction_id": from_junction_id,
        "to_junction_id": to_junction_id,
        "suggested_route": route_result["suggested_route"],
        "total_distance_km": route_result["total_distance_km"],
        "reasons": explain_route(from_junction_id, to_junction_id, route_result, roads, junctions),
        "route_request": save_result["data"]
    }


if __name__ == "__main__":
    print("Route Optimization Agent is ready.")
