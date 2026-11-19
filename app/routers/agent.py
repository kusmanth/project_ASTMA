"""Agent API: lets the frontend use the agents (instead of typing commands in Git Bash)."""
import asyncio
import sys

from fastapi import APIRouter, HTTPException
from google.genai import errors as ai_errors
from pydantic import BaseModel, Field

from agents.executor import execute
from agents.mcp_server import find_junction_by_name
from agents.orchestrator import make_plan
from agents.route_optimization import optimize_route
from agents.traffic_monitoring import monitor_traffic
from agents.traffic_signal import manage_signal_timings

router = APIRouter(prefix="/agents", tags=["Agents"])

# Task names come from the knowledge document file names in agents/knowledge/
TRAFFIC_TASK = "Check traffic on roads"
ROUTE_TASK = "Request a route"


class RouteOptimizationRequest(BaseModel):
    user_id: int
    from_junction_id: int
    to_junction_id: int


class PlanRequest(BaseModel):
    request: str = Field(min_length=3, max_length=500)
    user_id: int = Field(gt=0)


class ExecuteRequest(BaseModel):
    plan: dict
    user_id: int = Field(gt=0)


# ---------- Chat: Orchestrator (Agent 1) + the agent that does the work ----------

def run_executor(plan: dict, user_id: int) -> str:
    """The MCP Executor is async and starts the MCP server as a small background program.
    On Windows that needs the Proactor event loop, so we run it in its own loop."""
    loop_factory = asyncio.ProactorEventLoop if sys.platform == "win32" else None
    return asyncio.run(execute(plan, user_id), loop_factory=loop_factory)


def junction_id(name: str) -> int:
    result = find_junction_by_name(name)
    if result["status_code"] != 200:
        raise ValueError(f"Junction '{name}' not found")
    return result["data"][0]["id"]


def real_error(error: Exception) -> Exception:
    """The MCP client wraps errors in a group ("unhandled errors in a TaskGroup"). Get the real one."""
    while isinstance(error, BaseExceptionGroup) and error.exceptions:
        error = error.exceptions[0]
    return error


def agent_error(error: Exception, prefix: str) -> HTTPException:
    """Turn any agent error into a clear message for the user."""
    error = real_error(error)
    if isinstance(error, ai_errors.APIError) and error.code == 429:
        return HTTPException(status_code=429, detail="AI quota reached for today. Please try again later.")
    if isinstance(error, ai_errors.ServerError):
        return HTTPException(status_code=503, detail="The AI service is busy right now. Please try again in a minute.")
    if isinstance(error, (ValueError, KeyError)):
        return HTTPException(status_code=400, detail=str(error))
    return HTTPException(status_code=502, detail=f"{prefix}: {error}")


@router.post("/plan")
def create_plan(body: PlanRequest):
    """Agent 1: understand the request and return a plan. Nothing is changed yet."""
    try:
        return make_plan(body.request, body.user_id)
    except Exception as error:
        raise agent_error(error, "Orchestrator failed")


@router.post("/execute")
def execute_plan(body: ExecuteRequest):
    """Run an approved plan with the right agent."""
    plan = body.plan
    task = plan.get("task")
    if not task:
        raise HTTPException(status_code=400, detail="This plan has no task")
    if plan.get("missing"):
        raise HTTPException(status_code=400, detail=f"Please include: {', '.join(plan['missing'])}")
    try:
        if task == TRAFFIC_TASK:
            return {"agent": "traffic_monitoring", "result": monitor_traffic()}
        if task == ROUTE_TASK:
            details = plan.get("details", {})
            result = optimize_route(
                user_id=body.user_id,
                from_junction_id=junction_id(details["from_junction"]),
                to_junction_id=junction_id(details["to_junction"]),
            )
            return {"agent": "route_optimization", "result": result}
        return {"agent": "executor", "result": run_executor(plan, body.user_id)}
    except Exception as error:
        raise agent_error(error, "Agent failed")


# ---------- Direct buttons for each agent ----------

@router.post("/traffic-monitoring/run")
def run_traffic_monitoring():
    """Execute the Traffic Monitoring Agent."""
    try:
        return {"message": "Traffic Monitoring Agent executed successfully", "results": monitor_traffic()}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/traffic-signal/run")
def run_traffic_signal():
    """Execute the Traffic Signal Agent."""
    try:
        manage_signal_timings()
        return {"message": "Traffic Signal Agent executed successfully"}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.post("/route-optimization/run")
def run_route_optimization(request: RouteOptimizationRequest):
    """Execute the Route Optimization Agent."""
    try:
        return optimize_route(user_id=request.user_id, from_junction_id=request.from_junction_id,
                              to_junction_id=request.to_junction_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))