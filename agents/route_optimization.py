
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

        graph[start].append((end, distance, road["id"]))
        graph[end].append((start, distance, road["id"]))

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
        "route_request": save_result["data"]
    }


if __name__ == "__main__":
    print("Route Optimization Agent is ready.")
