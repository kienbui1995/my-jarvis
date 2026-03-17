"""MCP Loader — discover and cache MCP tools, create LangChain wrappers."""
import asyncio
import json
import logging
from uuid import UUID

from langchain_core.tools import StructuredTool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import core.redis as redis_pool
from db.models import MCPServer
from mcp.proxy import proxy_call_tool, proxy_discover_tools

logger = logging.getLogger(__name__)

CACHE_TTL = 3600


async def _get_cached_tools(user_id: str) -> list[dict] | None:
    r = redis_pool.get()
    cached = await r.get(f"mcp_tools:{user_id}")
    if cached:
        return json.loads(cached)
    return None


async def _set_cached_tools(user_id: str, tools: list[dict]):
    r = redis_pool.get()
    await r.setex(f"mcp_tools:{user_id}", CACHE_TTL, json.dumps(tools))


async def invalidate_cache(user_id: str):
    r = redis_pool.get()
    await r.delete(f"mcp_tools:{user_id}")


async def load_mcp_tools(user_id: str, tier: str, conv_id: str, db: AsyncSession) -> list[StructuredTool]:
    servers = (await db.execute(
        select(MCPServer).where(MCPServer.user_id == UUID(user_id), MCPServer.enabled == True)  # noqa: E712
    )).scalars().all()

    if not servers:
        return []

    cached = await _get_cached_tools(user_id)
    if cached:
        return _build_tools_from_cache(cached, servers, user_id, tier, conv_id)

    discoveries = await asyncio.gather(
        *[proxy_discover_tools(srv) for srv in servers],
        return_exceptions=True,
    )

    all_tool_defs = []
    tools = []
    seen_names = set()

    for srv, disc in zip(servers, discoveries):
        if isinstance(disc, Exception):
            logger.warning(f"MCP discovery failed for {srv.name}: {disc}")
            continue
        for t in disc:
            tool_name = f"mcp_{srv.name}_{t['name']}"
            if tool_name in seen_names:
                tool_name = f"{tool_name}_{str(srv.id)[:4]}"
            seen_names.add(tool_name)

            all_tool_defs.append({
                "server_id": str(srv.id),
                "server_name": srv.name,
                "name": t["name"],
                "tool_name": tool_name,
                "description": t.get("description", ""),
            })

            tools.append(_make_tool(tool_name, t, srv, user_id, tier, conv_id))

    await _set_cached_tools(user_id, all_tool_defs)
    return tools


def _build_tools_from_cache(
    cached: list[dict], servers: list[MCPServer], user_id: str, tier: str, conv_id: str
) -> list[StructuredTool]:
    srv_map = {str(s.id): s for s in servers}
    tools = []
    for td in cached:
        srv = srv_map.get(td["server_id"])
        if not srv:
            continue
        tools.append(_make_tool(td["tool_name"], {"name": td["name"], "description": td["description"]}, srv, user_id, tier, conv_id))
    return tools


def _make_tool(
    tool_name: str, tool_def: dict, server: MCPServer,
    user_id: str, tier: str, conv_id: str,
) -> StructuredTool:
    _srv, _name, _uid, _tier, _cid = server, tool_def["name"], user_id, tier, conv_id

    async def _call(s=_srv, n=_name, u=_uid, t=_tier, c=_cid, **kwargs):
        return await proxy_call_tool(s, n, kwargs, u, c, t)

    return StructuredTool.from_function(
        func=lambda **kwargs: None,
        coroutine=_call,
        name=tool_name,
        description=tool_def.get("description", f"MCP tool: {tool_def['name']}"),
    )
