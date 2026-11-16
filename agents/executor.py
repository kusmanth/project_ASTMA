"""Agent 2: MCP executor. Performs the plan by calling our APIs through the MCP server."""
import json
import sys

from google.genai import types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from agents.llm import CHAT_MODEL, client

INSTRUCTIONS = """You are the Executor agent of ASTMA, a smart traffic management system.
Carry out the plan step by step using the tools. Use the real ids returned by the tools.
Rules:
- Follow the steps in order. Do not skip any check.
- If a tool returns a status_code of 400 or more, or a check fails, STOP and explain why in one or two sentences.
- Never invent ids or values.
- When done, reply in 1-3 short sentences saying what was done (include the new id)."""

SERVER = StdioServerParameters(command=sys.executable, args=["-m", "agents.mcp_server"])


async def execute(plan: dict, user_id: int) -> str:
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            response = await client.aio.models.generate_content(
                model=CHAT_MODEL,
                contents=f"Current user id: {user_id}\nPlan:\n{json.dumps(plan, indent=2)}",
                config=types.GenerateContentConfig(
                    system_instruction=INSTRUCTIONS,
                    tools=[session],
                    temperature=0,
                ),
            )
            return response.text