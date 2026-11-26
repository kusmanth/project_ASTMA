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

    for signal in db.scalars(select(Signal).where(Signal.junction_id.in_(route_junctions))):
        if not signal.is_active:
            continue
        signal.current_state = "green" if signal.road_id in trip.route else "red"


def close_corridor(trip: EmergencyTrip, db: Session) -> None:
    if not trip.route:
        return
    for signal in db.scalars(select(Signal).where(Signal.road_id.in_(trip.route))):
        signal.current_state = "red"
