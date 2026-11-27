"""Green corridor: clear the way for an emergency vehicle.

When a trip starts, we find the shortest route (Dijkstra, same as the Route Optimization Agent).
Every road on that route gets its signal turned GREEN, and the other signals at those
junctions turn RED, so cross traffic stops. When the trip ends, the route signals go back to red.
"""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from agents.route_optimization import find_shortest_route
from app.models import EmergencyTrip, Junction, Road, Signal


def open_corridor(trip: EmergencyTrip, db: Session) -> None:
    roads = db.scalars(select(Road)).all()
    junctions = db.scalars(select(Junction)).all()
    try:
        result = find_shortest_route(
            trip.from_junction_id,
            trip.to_junction_id,
            [dict(id=r.id, from_junction_id=r.from_junction_id, to_junction_id=r.to_junction_id,
                  distance_km=float(r.distance_km), is_active=r.is_active) for r in roads],
            [dict(id=j.id, is_active=j.is_active) for j in junctions],
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    trip.route = result["suggested_route"]
    road_to_junction = {r.id: r.to_junction_id for r in roads}
    route_junctions = {road_to_junction[road_id] for road_id in trip.route}
    held = other_active_routes(trip, db)  # roads another emergency vehicle is still using

    for signal in db.scalars(select(Signal).where(Signal.junction_id.in_(route_junctions))):
        if not signal.is_active:
            continue
        if signal.road_id in trip.route or signal.road_id in held:
            signal.current_state = "green"
        else:
            signal.current_state = "red"


def close_corridor(trip: EmergencyTrip, db: Session) -> None:
    if not trip.route:
        return
    held = other_active_routes(trip, db)
    for signal in db.scalars(select(Signal).where(Signal.road_id.in_(trip.route))):
        if signal.road_id not in held:  # never switch off a road another active trip needs
            signal.current_state = "red"


def other_active_routes(trip: EmergencyTrip, db: Session) -> set[int]:
    roads = set()
    for other in db.scalars(select(EmergencyTrip).where(EmergencyTrip.status == "active")):
        if other.id != trip.id:
            roads.update(other.route or [])
    return roads
