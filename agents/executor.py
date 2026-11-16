"""Agent 2: MCP executor. Performs the plan by calling our APIs through the MCP server.

The loop, step by step:
1. Start the MCP server and ask it for its list of tools (the "menu").
2. Send Gemini the plan + the menu.
3. If Gemini asks for a tool, the MCP client calls it on the server and sends the result back.
4. Repeat until Gemini answers with plain text (the final answer).
"""
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
MAX_ROUNDS = 10  # safety limit, so Gemini can never loop forever


async def execute(plan: dict, user_id: int) -> str:
    async with stdio_client(SERVER) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1. Get the menu from the MCP server and describe it to Gemini
            menu = await session.list_tools()
            declarations = [
                types.FunctionDeclaration(name=t.name, description=t.description or "",
                                          parameters_json_schema=t.inputSchema)
                for t in menu.tools
            ]
            config = types.GenerateContentConfig(
                system_instruction=INSTRUCTIONS,
                tools=[types.Tool(function_declarations=declarations)],
                temperature=0,
            )

            # 2. The conversation starts with the plan
            history = [types.Content(role="user", parts=[types.Part(
                text=f"Current user id: {user_id}\nPlan:\n{json.dumps(plan, indent=2)}")])]

            for _ in range(MAX_ROUNDS):
                response = await client.aio.models.generate_content(
                    model=CHAT_MODEL, contents=history, config=config)

                # 4. No tool requested: this is the final answer
                if not response.function_calls:
                    return response.text

                # 3. Gemini ordered tools: run each one on the MCP server
                history.append(response.candidates[0].content)
                results = []
                for call in response.function_calls:
                    args = dict(call.args or {})
                    print(f"  [tool] {call.name}({args})")
                    result = await session.call_tool(call.name, args)
                    text = "".join(c.text for c in result.content if c.type == "text")
                    results.append(types.Part.from_function_response(name=call.name, response={"result": text}))
                history.append(types.Content(role="user", parts=results))

            return "Stopped: too many tool calls."