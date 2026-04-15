"""MCP Client — connect to external MCP servers, discover tools, proxy calls.

Supports stdio transport (subprocess) and SSE transport (HTTP).
"""
import asyncio
import json
import logging
from uuid import UUID

from langchain_core.tools import StructuredTool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import MCPServer

logger = logging.getLogger(__name__)


class MCPStdioTransport:
    """Connect to MCP server via stdio (subprocess)."""

    def __init__(self, command: str, args: list[str] | None = None):
        self.command = command
        self.args = args or []
        self._proc: asyncio.subprocess.Process | None = None
        self._req_id = 0

    async def start(self):
        self._proc = await asyncio.create_subprocess_exec(
            self.command, *self.args,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )

    async def send(self, method: str, params: dict | None = None) -> dict:
        if not self._proc or not self._proc.stdin or not self._proc.stdout:
            raise RuntimeError("Transport not started")
        self._req_id += 1
        msg = json.dumps({"jsonrpc": "2.0", "id": self._req_id, "method": method, "params": params or {}})
        self._proc.stdin.write((msg + "\n").encode())
        await self._proc.stdin.drain()
        line = await asyncio.wait_for(self._proc.stdout.readline(), timeout=30)
        return json.loads(line)

    async def close(self):
        if self._proc:
            self._proc.terminate()
            await self._proc.wait()


class MCPSSETransport:
    """Connect to MCP server via SSE (HTTP)."""

    def __init__(self, url: str):
        self.url = url

    async def start(self):
        pass  # SSE is stateless per-request

    async def send(self, method: str, params: dict | None = None) -> dict:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                return await resp.json()

    async def close(self):
        pass


def _create_transport(server: MCPServer):
    config = server.config or {}
    if server.transport == "stdio":
        return MCPStdioTransport(config.get("command", ""), config.get("args", []))
    elif server.transport == "sse":
        return MCPSSETransport(config.get("url", ""))
    raise ValueError(f"Unknown transport: {server.transport}")


async def discover_tools(server: MCPServer) -> list[dict]:
    """Call MCP server's tools/list, return tool definitions."""
    transport = _create_transport(server)
    try:
        await transport.start()
        resp = await transport.send("tools/list")
        return resp.get("result", {}).get("tools", [])
    except Exception:
        logger.exception(f"MCP discover failed: {server.name}")
        return []
    finally:
        await transport.close()


async def call_tool(server: MCPServer, tool_name: str, arguments: dict) -> str:
    """Proxy a tool call to MCP server."""
    transport = _create_transport(server)
    try:
        await transport.start()
        resp = await transport.send("tools/call", {"name": tool_name, "arguments": arguments})
        result = resp.get("result", {})
        content = result.get("content", [])
        return "\n".join(c.get("text", str(c)) for c in content) if content else json.dumps(result)
    except Exception:
        logger.exception(f"MCP call failed: {server.name}/{tool_name}")
        return f"Error calling MCP tool {tool_name}"
    finally:
        await transport.close()


async def call_mcp_tool(user_id: str, server_id: str, tool_name: str, arguments: dict) -> str:
    """High-level: find user's MCP server by id, call a tool on it."""
    from db.session import async_session
    async with async_session() as db:
        server = (await db.execute(
            select(MCPServer).where(MCPServer.user_id == UUID(user_id), MCPServer.name == server_id, MCPServer.enabled == True)  # noqa: E712
        )).scalar_one_or_none()
    if not server:
        return ""
    return await call_tool(server, tool_name, arguments)


async def get_mcp_tools(user_id: str, db: AsyncSession) -> list[StructuredTool]:
    """Load all enabled MCP servers for user, discover tools, return as LangChain tools.
    NOTE: Superseded by mcp.loader — kept for backward compatibility."""
    servers = (await db.execute(select(MCPServer).where(MCPServer.user_id == UUID(user_id), MCPServer.enabled == True))).scalars().all()  # noqa: E712
    tools = []
    for srv in servers:
        try:
            mcp_tools = await discover_tools(srv)
            for t in mcp_tools:
                _srv, _name = srv, t["name"]

                async def _call(s=_srv, n=_name, **kwargs):
                    return await call_tool(s, n, kwargs)

                tools.append(StructuredTool.from_function(
                    func=lambda **kwargs: None,
                    coroutine=_call,
                    name=f"mcp_{srv.name}_{t['name']}",
                    description=t.get("description", f"MCP tool: {t['name']}"),
                ))
        except Exception:
            logger.exception(f"Failed to load MCP tools from {srv.name}")
    return tools
