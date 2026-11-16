
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from agents.traffic_monitoring import monitor_traffic
from agents.traffic_signal import manage_signal_timings
from agents.route_optimization import optimize_route

router = APIRouter(
    prefix="/agents",
    tags=["Agents"]
)


class RouteOptimizationRequest(BaseModel):
    user_id: int
    from_junction_id: int
    to_junction_id: int


@router.post("/traffic-monitoring/run")
def run_traffic_monitoring():
    """Execute the Traffic Monitoring Agent."""
    try:
        result = monitor_traffic()

        return {
            "message": "Traffic Monitoring Agent executed successfully",
            "results": result
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/traffic-signal/run")
def run_traffic_signal():
    """Execute the Traffic Signal Agent."""
    try:
        manage_signal_timings()

        return {
            "message": "Traffic Signal Agent executed successfully"
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/route-optimization/run")
def run_route_optimization(request: RouteOptimizationRequest):
    """Execute the Route Optimization Agent."""
    try:
        result = optimize_route(
            user_id=request.user_id,
            from_junction_id=request.from_junction_id,
            to_junction_id=request.to_junction_id
        )

        return result

    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

