"""MCP Proxy — sanitize, rate limit, SSRF protection, audit logging, security hardening."""
import html
import logging
import re
import time
from ipaddress import ip_address
from urllib.parse import urlparse

import core.redis as redis_pool
from core.evidence import log_evidence
from db.models import MCPServer
from mcp.client import call_tool as raw_call_tool, discover_tools as raw_discover_tools

logger = logging.getLogger(__name__)

MAX_OUTPUT_CHARS = 5000
BLOCKED_PATTERNS = re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
TIER_LIMITS = {"free": 10, "pro": 60, "pro_plus": 120}

# V8: Prompt injection patterns in tool descriptions (Hermes-inspired)
INJECTION_PATTERNS = re.compile(
    r"(ignore previous|ignore all|system prompt|you are now|forget your|override instruction|disregard)",
    re.IGNORECASE,
)


def _is_internal_url(url: str) -> bool:
    try:
        host = urlparse(url).hostname
        if not host:
            return True
        if host in ("localhost", "127.0.0.1", "0.0.0.0", "metadata.google.internal"):
            return True
        ip = ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except (ValueError, TypeError):
        return False


def _sanitize_output(text: str) -> str:
    text = BLOCKED_PATTERNS.sub("", text)
    text = html.unescape(text)
    if len(text) > MAX_OUTPUT_CHARS:
        text = text[:MAX_OUTPUT_CHARS] + "\n... (truncated)"
    return text


async def _check_rate_limit(user_id: str, server_name: str, tier: str) -> bool:
    limit = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    r = redis_pool.get()
    now = int(time.time())
    key = f"mcp_rate:{user_id}:{server_name}:{now // 60}"
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, 120)
    count, _ = await pipe.execute()
    return count <= limit


async def proxy_discover_tools(server: MCPServer) -> list[dict]:
    url = (server.config or {}).get("url", "")
    if server.transport == "sse" and _is_internal_url(url):
        logger.warning(f"MCP SSRF blocked: {server.name} → {url}")
        return []
    tools = await raw_discover_tools(server)

    # V8: Scan tool descriptions for prompt injection patterns
    safe_tools = []
    for t in tools:
        desc = t.get("description", "")
        if INJECTION_PATTERNS.search(desc):
            logger.warning(f"MCP tool description injection blocked: {server.name}/{t.get('name')} — '{desc[:100]}'")
            continue
        safe_tools.append(t)

    return safe_tools


async def proxy_call_tool(
    server: MCPServer,
    tool_name: str,
    arguments: dict,
    user_id: str,
    conv_id: str = "",
    tier: str = "free",
) -> str:
    if not await _check_rate_limit(user_id, server.name, tier):
        return f"Rate limit exceeded for MCP server {server.name}. Vui lòng thử lại sau."

    url = (server.config or {}).get("url", "")
    if server.transport == "sse" and _is_internal_url(url):
        return "MCP server URL blocked (internal network)."

    t0 = time.monotonic()
    result = await raw_call_tool(server, tool_name, arguments)
    duration_ms = int((time.monotonic() - t0) * 1000)

    result = _sanitize_output(result)

    await log_evidence(
        user_id, conv_id, "mcp_proxy", "mcp_tool_call",
        tool_name=f"mcp_{server.name}_{tool_name}",
        tool_input=arguments,
        tool_output=result[:500],
        duration_ms=duration_ms,
    )

    return result
