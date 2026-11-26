
"""Traffic Signal Agent: adjusts signal timings based on traffic congestion."""

from datetime import datetime

from agents.traffic_monitoring import monitor_traffic
from agents.mcp_server import get_signals, get_signal_timings, update_signal_timing


def is_active_timing(timing: dict, current_time) -> bool:
    """Check whether the timing record is active at the current time."""

    start = datetime.strptime(
        timing["start_time"][:8], "%H:%M:%S"
    ).time()

    end = datetime.strptime(
        timing["end_time"][:8], "%H:%M:%S"
    ).time()

    if start <= end:
        return start <= current_time <= end

    return current_time >= start or current_time <= end


def get_green_time(traffic_status: str) -> int:
    """Return green signal duration based on congestion."""

    timings = {
        "low": 30,
        "medium": 45,
        "high": 60
    }

    return timings.get(traffic_status, 0)


def manage_signal_timings() -> list:
    """Adjust signal timings according to traffic conditions."""

    print("\n===== TRAFFIC SIGNAL AGENT =====")

    traffic_reports = monitor_traffic()

    signals_result = get_signals()
    timings_result = get_signal_timings()

    if signals_result["status_code"] != 200:
        raise RuntimeError("Could not retrieve traffic signals.")

    if timings_result["status_code"] != 200:
        raise RuntimeError("Could not retrieve signal timings.")

    signals = signals_result["data"] or []
    timings = timings_result["data"] or []

    current_time = datetime.now().time()

    for report in traffic_reports:

        road_id = report["road_id"]
        traffic_status = report["traffic_status"]

        if traffic_status not in ["low", "medium", "high"]:
            print(f"\nRoad {road_id}: No recent traffic data. Skipping.")
            continue

        matching_signals = [
            signal for signal in signals
            if signal["road_id"] == road_id and signal["is_active"]
        ]

        if not matching_signals:
            print(f"\nRoad {road_id}: No active signal found.")
            continue

        for signal in matching_signals:

            signal_id = signal["id"]

            matching_timings = [
                timing for timing in timings
                if timing["signal_id"] == signal_id
                and is_active_timing(timing, current_time)
            ]

            if not matching_timings:
                print(f"\nSignal {signal_id}: No active timing record.")
                continue

            timing = matching_timings[0]

            new_green_time = get_green_time(traffic_status)

            if timing["green_time"] == new_green_time:
                print(
                    f"\nSignal {signal_id}: Green time is already "
                    f"{new_green_time} seconds."
                )
                continue

            result = update_signal_timing(
                timing_id=timing["id"],
                signal_id=signal_id,
                start_time=timing["start_time"],
                end_time=timing["end_time"],
                green_time=new_green_time,
                yellow_time=5,
                red_time=timing["red_time"]
            )

            if result["status_code"] in [200, 201]:
                print(
                    f"\nSignal {signal_id} updated successfully."
                    f"\nTraffic status: {traffic_status}"
                    f"\nNew green time: {new_green_time} seconds"
                )
            else:
                print(
                    f"\nCould not update signal {signal_id}: "
                    f"{result['data']}"
                )

    # Step 2: the other roads at each junction wait longer (or shorter) to match
    return balance_red_times()


def balance_red_times() -> list:
    """At each junction the signals take turns: while one road is green, the others wait.

    So a road's red time = green + yellow of every OTHER road at the same junction.
    Example: greens 60, 30, 45 (yellow 5) -> reds 85, 115, 100.
    """

    signals = get_signals()["data"] or []
    timings = get_signal_timings()["data"] or []
    current_time = datetime.now().time()

    # junction id -> list of (signal, its active timing)
    junctions = {}
    for signal in signals:
        if not signal["is_active"]:
            continue
        active = [t for t in timings
                  if t["signal_id"] == signal["id"] and is_active_timing(t, current_time)]
        if active:
            junctions.setdefault(signal["junction_id"], []).append((signal, active[0]))

    changes = []
    for junction_id, pairs in junctions.items():
        if len(pairs) < 2:
            continue  # a single signal has nobody to take turns with

        cycle = sum(t["green_time"] + t["yellow_time"] for _, t in pairs)

        for signal, timing in pairs:
            new_red = cycle - (timing["green_time"] + timing["yellow_time"])
            if timing["red_time"] == new_red:
                continue
            result = update_signal_timing(
                timing_id=timing["id"], signal_id=signal["id"],
                start_time=timing["start_time"], end_time=timing["end_time"],
                green_time=timing["green_time"], yellow_time=timing["yellow_time"],
                red_time=new_red,
            )
            if result["status_code"] in [200, 201]:
                print(f"Junction {junction_id}, signal {signal['id']}: red time "
                      f"{timing['red_time']} -> {new_red} seconds")
                changes.append({"junction_id": junction_id, "signal_id": signal["id"],
                                "road_id": signal["road_id"], "green_time": timing["green_time"],
                                "old_red_time": timing["red_time"], "new_red_time": new_red})
    return changes


if __name__ == "__main__":
    try:
        manage_signal_timings()
    except Exception as error:
        print("Error:", error)
