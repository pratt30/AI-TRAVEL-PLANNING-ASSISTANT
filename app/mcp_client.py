import json
import sys
from pathlib import Path
from typing import Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "app" / "mcp_server.py"

async def call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    server = StdioServerParameters(command=sys.executable, args=[str(SERVER_PATH)], env=None)
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            if getattr(result, "structuredContent", None):
                return result.structuredContent
            if getattr(result, "content", None):
                for item in result.content:
                    if hasattr(item, "text"):
                        try:
                            return json.loads(item.text)
                        except json.JSONDecodeError:
                            return {"ok": False, "error": item.text}
            return {"ok": False, "error": "MCP returned no readable content."}
