"""Try both agents from Git Bash:
uv run python -m agents.run --user 1 "book emergency trip for TS09AB1234 from Ameerpet to Paradise, critical"
"""
import argparse
import asyncio
import json

from agents.executor import execute
from agents.orchestrator import make_plan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("request", help="what the user types")
    parser.add_argument("--user", type=int, required=True, help="id of the user making the request")
    args = parser.parse_args()

    print("\n[Agent 1: Orchestrator] searching the knowledge base...")
    plan = make_plan(args.request, args.user)
    print(json.dumps(plan, indent=2))

    if not plan.get("task"):
        print(plan.get("message"))
        return
    if plan.get("missing"):
        print(f"\nPlease include: {', '.join(plan['missing'])}")
        return
    if input("\nRun this plan? (y/n): ").strip().lower() != "y":
        print("Cancelled.")
        return

    print("\n[Agent 2: Executor] calling the APIs through MCP...")
    print(asyncio.run(execute(plan, args.user)))


if __name__ == "__main__":
    main()