"""What each traffic light is showing RIGHT NOW.

Normal mode: the signals at a junction take turns, in a fixed cycle, using their real timings.
  Signal 1 is green for its green time, then yellow, then signal 2 gets its turn, and so on.
  Everyone not on their turn is red. The clock decides where we are in the cycle,
  so every screen shows the same lights and they keep moving.

Emergency mode: if an ACTIVE emergency trip passes through the junction, the road the
  vehicle uses is held green and every other road there is red, until the trip ends.
  This wins over the normal cycle, and over any other agent.
"""
import time
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EmergencyTrip, Road, Signal, SignalTiming

DEFAULT_GREEN, DEFAULT_YELLOW = 45, 5


def _active_timing(timings: list[SignalTiming], now) -> SignalTiming | None:
    for t in timings:
        start, end = t.start_time, t.end_time
        if (start <= now <= end) if start <= end else (now >= start or now <= end):
            return t
    return None


def cycle_position(slots: list[tuple[int, int]], second: int) -> tuple[int, str, int]:
    """slots = [(green, yellow), ...] in turn order.
    Returns (whose turn, "green" or "yellow", seconds left in that colour)."""
    cycle = sum(g + y for g, y in slots)
    t = second % cycle
    for i, (green, yellow) in enumerate(slots):
        if t < green:
            return i, "green", green - t
        if t < green + yellow:
            return i, "yellow", green + yellow - t
        t -= green + yellow
    return 0, "green", slots[0][0]  # not reached


def live_states(db: Session) -> list[dict]:
    signals = [s for s in db.scalars(select(Signal).order_by(Signal.id)) if s.is_active]
    timings = db.scalars(select(SignalTiming)).all()
    road_end = {r.id: r.to_junction_id for r in db.scalars(select(Road))}

    # Roads held green by active emergency trips
    corridor_roads = set()
    for trip in db.scalars(select(EmergencyTrip).where(EmergencyTrip.status == "active")):
        corridor_roads.update(trip.route or [])
    corridor_junctions = {road_end[r] for r in corridor_roads if r in road_end}

    now = datetime.now().time()
    second = int(time.time())
    by_junction: dict[int, list[Signal]] = {}
    for s in signals:
        by_junction.setdefault(s.junction_id, []).append(s)

    result = []
    for junction_id, group in by_junction.items():
        if junction_id in corridor_junctions:
            for s in group:
                state = "green" if s.road_id in corridor_roads else "red"
                result.append(dict(signal_id=s.id, road_id=s.road_id, junction_id=junction_id,
                                   state=state, mode="emergency", seconds_left=None))
            continue

        slots = []
        for s in group:
            t = _active_timing([t for t in timings if t.signal_id == s.id], now)
            slots.append((t.green_time, t.yellow_time) if t else (DEFAULT_GREEN, DEFAULT_YELLOW))
        # Each junction starts its cycle at a different moment, like real junctions
        turn, colour, left = cycle_position(slots, second + junction_id * 17)
        cycle = sum(g + y for g, y in slots)
        for i, s in enumerate(group):
            if i == turn:
                state, seconds_left = colour, left
            else:
                # red until this signal's turn comes round
                ahead = (i - turn) % len(group)
                seconds_left = left + (slots[turn][1] if colour == "green" else 0) + sum(
                    slots[(turn + k) % len(group)][0] + slots[(turn + k) % len(group)][1] for k in range(1, ahead))
                seconds_left = seconds_left % cycle or cycle
                state = "red"
            result.append(dict(signal_id=s.id, road_id=s.road_id, junction_id=junction_id,
                               state=state, mode="normal", seconds_left=seconds_left))
    return result
