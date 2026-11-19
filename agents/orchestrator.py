"""Agent 1: Orchestrator (RAG). Finds the right task in the knowledge base and writes the plan."""
import json

from google.genai import types

from agents.llm import generate
from agents.rag import search_top

MAX_DISTANCE = 0.6  # above this, a task is not close enough to be a candidate
TOP_K = 2           # how many tasks RAG gives to Gemini to choose from

PROMPT = """You are the Orchestrator agent of ASTMA, a smart traffic management system.
A user sent a request. Our knowledge base found the candidate tasks below (closest first).
First choose the ONE task that really matches what the user wants. Read the whole request carefully:
for example, a trip that already reached or completed is NOT a new booking.
If no candidate fits, set "task" to null.
Then write a plan for the executor agent. Use ONLY the steps from the chosen task. Do not invent steps.

Return JSON with exactly these keys:
- "task": the chosen task name, exactly as written after ###, or null
- "reason": one short sentence on why you chose this task
- "details": an object with every detail the task needs, taken from the user's request
- "missing": a list of details that are needed but not in the request (empty list if none)
- "steps": the task's steps, rewritten with the real values filled in

Current user id: {user_id}

Candidate tasks:
{candidates}

User request: "{request}"
"""

CANT_HELP = {"task": None, "missing": [], "steps": [], "details": {},
             "message": "Sorry, I can't help with that yet."}


def make_plan(request: str, user_id: int) -> dict:
    # 1. RAG: find the closest tasks, keep only the ones that are close enough
    found = search_top(request, TOP_K)
    candidates = [(name, content, d) for name, content, d in found if d <= MAX_DISTANCE]
    if not candidates:
        return CANT_HELP

    # 2. Gemini: choose the right task and write the plan
    text = "\n\n".join(f"### {name}\n{content}" for name, content, _ in candidates)
    response = generate(
        contents=PROMPT.format(user_id=user_id, candidates=text, request=request),
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0),
    )
    plan = json.loads(response.text)

    # 3. Safety check: Gemini must pick one of our candidates
    names = [name for name, _, _ in candidates]
    if plan.get("task") not in names:
        return CANT_HELP
    plan["candidates"] = {name: round(d, 3) for name, _, d in candidates}
    return plan