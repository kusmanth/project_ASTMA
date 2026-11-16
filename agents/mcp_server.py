"""MCP server: our FastAPI endpoints as tools. The FastAPI server must be running."""

"""MCP server: our FastAPI endpoints as tools. The FastAPI server must be running."""
import os

import httpx
from mcp.server.fastmcp import FastMCP

API = os.getenv("ASTMA_API_URL", "http://127.0.0.1:8000")
mcp = FastMCP("astma")


def call(method: str, path: str, body: dict | None = None) -> dict:
    response = httpx.request(
        method,
        f"{API}{path}",
        json=body,
        timeout=15,
        follow_redirects=True
    )
    data = response.json() if response.content else None
    return {"status_code": response.status_code, "data": data}


@mcp.tool()
def get_user(user_id: int) -> dict:
    """Get one user by id, including user_type."""
    return call("GET", f"/users/{user_id}")


@mcp.tool()
def find_vehicle_by_number(vehicle_number: str) -> dict:
    """Find an emergency vehicle by its number."""
    result = call("GET", "/emergency-vehicles")
    wanted = vehicle_number.replace(" ", "").upper()
    matches = [
        v for v in result["data"] or []
        if v["vehicle_number"].replace(" ", "").upper() == wanted
    ]
    return {
        "status_code": 200 if matches else 404,
        "data": matches[0] if matches else "Vehicle not found"
    }


@mcp.tool()
def find_junction_by_name(name: str) -> dict:
    """Find a junction by part of its name."""
    result = call("GET", "/junctions")
    matches = [
        j for j in result["data"] or []
        if name.lower() in j["junction_name"].lower()
    ]
    return {
        "status_code": 200 if matches else 404,
        "data": matches or "Junction not found"
    }


@mcp.tool()
def list_roads() -> dict:
    """List all roads with their lane count and active status."""
    return call("GET", "/roads")


@mcp.tool()
def get_traffic_readings() -> dict:
    """Get all traffic readings. This tool only reads data."""
    return call("GET", "/traffic-readings")


@mcp.tool()
def create_emergency_trip(
    vehicle_id: int,
    created_by: int,
    from_junction_id: int,
    to_junction_id: int,
    urgency_level: str
) -> dict:
    """Start an emergency trip."""
    return call("POST", "/emergency-trips", {
        "vehicle_id": vehicle_id,
        "created_by": created_by,
        "from_junction_id": from_junction_id,
        "to_junction_id": to_junction_id,
        "urgency_level": urgency_level,
    })


@mcp.tool()
def update_emergency_trip_status(trip_id: int, status: str) -> dict:
    """End a trip. Status is completed or cancelled."""
    return call("PATCH", f"/emergency-trips/{trip_id}", {
        "status": status
    })


@mcp.tool()
def create_route_request(
    user_id: int,
    from_junction_id: int,
    to_junction_id: int,
    suggested_route: list[int]
) -> dict:
    """Save a route using an ordered list of road IDs."""
    return call("POST", "/route-requests", {
        "user_id": user_id,
        "from_junction_id": from_junction_id,
        "to_junction_id": to_junction_id,
        "suggested_route": suggested_route,
    })


if __name__ == "__main__":
    mcp.run()
