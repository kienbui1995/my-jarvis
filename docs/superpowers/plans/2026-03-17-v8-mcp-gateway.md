# V8.0 MCP Gateway — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Activate MCP pipeline with proxy layer, sandbox security, curated server registry (Google Workspace, GitHub, Notion), and frontend settings UI.

**Architecture:** MCP proxy wraps existing client.py transport layer — adds sanitization, rate limiting, SSRF protection, caching, and audit logging. Dynamic tool loader injects MCP tools into agent pipeline alongside 28 built-in tools. Frontend adds MCP tab to settings with curated server cards and per-tool toggles.

**Tech Stack:** Python (FastAPI, LangChain, Redis), TypeScript (Next.js, Zustand), PostgreSQL, asyncio

---

## File Structure

| Action | File | Purpose |
|--------|------|---------|
| Create | `backend/mcp/registry.py` | Curated MCP server definitions |
| Create | `backend/mcp/proxy.py` | Proxy layer: sanitize, rate limit, SSRF, audit |
| Create | `backend/mcp/loader.py` | Dynamic tool loading + cache |
| Modify | `backend/mcp/client.py` | Add URL validation to SSE transport |
| Modify | `backend/api/v1/mcp.py` | Add registry, tools, health, toggle endpoints |
| Modify | `backend/agent/nodes/agent_loop.py` | Bind MCP tools dynamically |
| Modify | `backend/agent/graph.py` | Add MCP tools to tools_node lookup |
| Modify | `backend/core/config.py` | Add MCP feature flag |
| Modify | `frontend/lib/api.ts` | Add MCP API methods |
| Modify | `frontend/app/(app)/settings/page.tsx` | Add MCP tab |

---

### Task 1: MCP Registry — Curated Server Definitions

**Files:**
- Create: `backend/mcp/registry.py`

- [ ] **Step 1: Create registry with 3 curated servers**

```python
# backend/mcp/registry.py
"""Curated MCP server registry — pre-configured servers users can enable."""

CURATED_SERVERS = [
    {
        "id": "google-workspace",
        "name": "Google Workspace",
        "description": "Google Calendar, Gmail, Drive — quản lý lịch, email, tài liệu",
        "transport": "sse",
        "default_config": {"url": "https://mcp.googleapis.com/v1"},
        "required_fields": ["api_key"],
        "icon": "google",
        "category": "productivity",
    },
    {
        "id": "github",
        "name": "GitHub",
        "description": "Repositories, Issues, PRs — quản lý code và dự án",
        "transport": "sse",
        "default_config": {"url": "https://api.githubcopilot.com/mcp"},
        "required_fields": ["api_key"],
        "icon": "github",
        "category": "developer",
    },
    {
        "id": "notion",
        "name": "Notion",
        "description": "Pages, Databases, Blocks — ghi chú và quản lý kiến thức",
        "transport": "sse",
        "default_config": {"url": "https://mcp.notion.so/v1"},
        "required_fields": ["api_key"],
        "icon": "notion",
        "category": "productivity",
    },
]


def get_registry() -> list[dict]:
    return CURATED_SERVERS


def get_curated_server(server_id: str) -> dict | None:
    return next((s for s in CURATED_SERVERS if s["id"] == server_id), None)
```

- [ ] **Step 2: Commit**

```bash
git add backend/mcp/registry.py
git commit -m "feat(mcp): add curated server registry (Google, GitHub, Notion)"
```

---

### Task 2: MCP Proxy — Sandbox Layer

**Files:**
- Create: `backend/mcp/proxy.py`

- [ ] **Step 1: Create proxy with sanitize + rate limit + SSRF + audit**

```python
# backend/mcp/proxy.py
"""MCP Proxy — sanitize, rate limit, SSRF protection, audit logging."""
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
TIER_LIMITS = {"free": 10, "pro": 60, "pro_plus": 120}  # calls per minute per server


def _is_internal_url(url: str) -> bool:
    """Block internal network access (SSRF protection)."""
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
    """Strip scripts, limit length."""
    text = BLOCKED_PATTERNS.sub("", text)
    text = html.unescape(text)
    if len(text) > MAX_OUTPUT_CHARS:
        text = text[:MAX_OUTPUT_CHARS] + "\n... (truncated)"
    return text


async def _check_rate_limit(user_id: str, server_name: str, tier: str) -> bool:
    """Sliding window rate limit per user per MCP server."""
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
    """Discover tools with SSRF check."""
    url = (server.config or {}).get("url", "")
    if server.transport == "sse" and _is_internal_url(url):
        logger.warning(f"MCP SSRF blocked: {server.name} → {url}")
        return []
    return await raw_discover_tools(server)


async def proxy_call_tool(
    server: MCPServer,
    tool_name: str,
    arguments: dict,
    user_id: str,
    conv_id: str = "",
    tier: str = "free",
) -> str:
    """Call MCP tool with rate limit, sanitize, audit."""
    # Rate limit
    if not await _check_rate_limit(user_id, server.name, tier):
        return f"Rate limit exceeded for MCP server {server.name}. Vui lòng thử lại sau."

    # SSRF check
    url = (server.config or {}).get("url", "")
    if server.transport == "sse" and _is_internal_url(url):
        return "MCP server URL blocked (internal network)."

    t0 = time.monotonic()
    result = await raw_call_tool(server, tool_name, arguments)
    duration_ms = int((time.monotonic() - t0) * 1000)

    # Sanitize
    result = _sanitize_output(result)

    # Audit log
    await log_evidence(
        user_id, conv_id, "mcp_proxy", "mcp_tool_call",
        tool_name=f"mcp_{server.name}_{tool_name}",
        tool_input=arguments,
        tool_output=result[:500],
        duration_ms=duration_ms,
    )

    return result
```

- [ ] **Step 2: Commit**

```bash
git add backend/mcp/proxy.py
git commit -m "feat(mcp): add proxy layer with sanitize, rate limit, SSRF, audit"
```

---

### Task 3: MCP Loader — Dynamic Tool Binding

**Files:**
- Create: `backend/mcp/loader.py`

- [ ] **Step 1: Create loader with parallel discovery + Redis cache**

```python
# backend/mcp/loader.py
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

CACHE_TTL = 3600  # 1 hour


async def _get_cached_tools(user_id: str) -> list[dict] | None:
    """Check Redis for cached tool definitions."""
    r = redis_pool.get()
    cached = await r.get(f"mcp_tools:{user_id}")
    if cached:
        return json.loads(cached)
    return None


async def _set_cached_tools(user_id: str, tools: list[dict]):
    r = redis_pool.get()
    await r.setex(f"mcp_tools:{user_id}", CACHE_TTL, json.dumps(tools))


async def invalidate_cache(user_id: str):
    """Called when user adds/removes/toggles MCP server."""
    r = redis_pool.get()
    await r.delete(f"mcp_tools:{user_id}")


async def load_mcp_tools(user_id: str, tier: str, conv_id: str, db: AsyncSession) -> list[StructuredTool]:
    """Load MCP tools for user — parallel discovery, cached, with proxy."""
    servers = (await db.execute(
        select(MCPServer).where(MCPServer.user_id == UUID(user_id), MCPServer.enabled == True)  # noqa: E712
    )).scalars().all()

    if not servers:
        return []

    # Check cache
    cached = await _get_cached_tools(user_id)
    if cached:
        return _build_tools_from_cache(cached, servers, user_id, tier, conv_id)

    # Parallel discovery
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

    # Cache
    await _set_cached_tools(user_id, all_tool_defs)

    return tools


def _build_tools_from_cache(
    cached: list[dict], servers: list[MCPServer], user_id: str, tier: str, conv_id: str
) -> list[StructuredTool]:
    """Rebuild LangChain tools from cached definitions."""
    srv_map = {str(s.id): s for s in servers}
    tools = []
    for td in cached:
        srv = srv_map.get(td["server_id"])
        if not srv:
            continue
        tools.append(_make_tool(
            td["tool_name"],
            {"name": td["name"], "description": td["description"]},
            srv, user_id, tier, conv_id,
        ))
    return tools


def _make_tool(
    tool_name: str, tool_def: dict, server: MCPServer,
    user_id: str, tier: str, conv_id: str,
) -> StructuredTool:
    _srv, _name, _uid, _tier, _cid = server, tool_def["name"], user_id, tier, conv_id
    return StructuredTool.from_function(
        func=lambda **kwargs: None,
        coroutine=lambda **kwargs, s=_srv, n=_name, u=_uid, t=_tier, c=_cid: proxy_call_tool(s, n, kwargs, u, c, t),
        name=tool_name,
        description=tool_def.get("description", f"MCP tool: {tool_def['name']}"),
    )
```

- [ ] **Step 2: Commit**

```bash
git add backend/mcp/loader.py
git commit -m "feat(mcp): add dynamic tool loader with parallel discovery + Redis cache"
```

---

### Task 4: Agent Integration — Bind MCP Tools

**Files:**
- Modify: `backend/core/config.py`
- Modify: `backend/agent/nodes/agent_loop.py`
- Modify: `backend/agent/graph.py`

- [ ] **Step 1: Add MCP feature flag to config**

In `backend/core/config.py`, add after other feature flags:

```python
MCP_GATEWAY_ENABLED: bool = True
```

- [ ] **Step 2: Modify agent_loop to dynamically bind MCP tools**

Replace `backend/agent/nodes/agent_loop.py`:

```python
"""Agent loop node — core LLM reasoning with tool calling."""
from langchain_core.messages import SystemMessage

from agent.state import AgentState
from agent.tools import all_tools
from core.context_guard import guard_context
from llm.cache import with_cache_control
from llm.gateway import get_llm

SYSTEM_PROMPT = """Bạn là MY JARVIS — trợ lý AI cá nhân thông minh, nói tiếng Việt tự nhiên.

{user_preferences}

Nguyên tắc:
- Trả lời ngắn gọn, thân thiện, đúng trọng tâm
- Dùng tool khi cần hành động — LUÔN ưu tiên tool thay vì trả lời chung chung
- Luôn nhớ context của user từ memory
- Nếu không chắc, hỏi lại thay vì đoán
- KHÔNG BAO GIỜ hỏi user_id — hệ thống tự inject
- Nếu tool lỗi, thử tool khác hoặc giải thích lỗi rõ ràng
- Tool có prefix "mcp_" là từ MCP server bên ngoài — dùng khi built-in tools không đủ

Hướng dẫn chọn tool:
- "thời tiết/nhiệt độ/trời mưa" → weather_vn
- "tin tức/báo/news" → news_vn
- "task/việc/công việc/deadline" → task_create/task_list/task_update
- "lịch/hẹn/cuộc họp/meeting" → calendar_create/calendar_list hoặc google_calendar_list
- "email/mail" → gmail_read/gmail_send/gmail_reply
- "nhớ/lưu/ghi nhớ" → memory_save | "nhớ gì/biết gì về" → memory_search
- "ghi chú/note/memo" → note_save/note_search/note_list
- "chi tiêu/tiền/mua" → expense_log | "ngân sách/budget" → budget_check
- "tìm/search/tra cứu" → web_search | "tóm tắt URL/link" → summarize_url
- "mở trang/xem web/browse" → browse_web | "chụp trang" → browse_screenshot
- "ảnh/hình/file/hóa đơn" → analyze_file/ocr_file
- Câu hỏi đơn giản (chào, hỏi giờ, nói chuyện) → trả lời trực tiếp, KHÔNG dùng tool

{hot_memory}
{cold_memory}"""


async def agent_loop_node(state: AgentState) -> dict:
    """Call routed LLM with tools bound. Returns AIMessage (possibly with tool_calls)."""
    model = state.get("selected_model", "gemini-2.0-flash")

    # Combine built-in + MCP tools
    tools = list(all_tools)
    mcp_tools = state.get("mcp_tools", [])
    if mcp_tools:
        tools.extend(mcp_tools)

    llm = get_llm(model).bind_tools(tools)

    sys_prompt = SYSTEM_PROMPT.format(
        hot_memory=state.get("hot_memory", ""),
        cold_memory=state.get("cold_memory", ""),
        user_preferences=state.get("user_preferences", ""),
    )

    messages = [SystemMessage(content=sys_prompt)] + state["messages"]
    messages = with_cache_control(messages, model)
    messages = guard_context(messages, model)

    response = await llm.ainvoke(messages)
    return {"messages": [response]}
```

- [ ] **Step 3: Add mcp_tools to AgentState**

In `backend/agent/state.py`, add field:

```python
mcp_tools: list = []
```

- [ ] **Step 4: Modify tools_node to handle MCP tools**

In `backend/agent/graph.py`, update `tools_node` to look up MCP tools dynamically. After `_tools_by_name` lookup fails, check `state.get("mcp_tools")`:

Add after line 67-69 (`tool = _tools_by_name.get(tc["name"])`):

```python
        if not tool:
            # Check MCP tools
            mcp_tools = state.get("mcp_tools", [])
            tool = next((t for t in mcp_tools if t.name == tc["name"]), None)
        if not tool:
            results.append(ToolMessage(content=f"Tool {tc['name']} not found", tool_call_id=tc["id"]))
            continue
```

- [ ] **Step 5: Load MCP tools in router_node**

In `backend/agent/nodes/router.py`, after memory loading (line ~155), add MCP tool loading:

```python
    # Load MCP tools
    mcp_tools = []
    if user_id and settings.MCP_GATEWAY_ENABLED:
        try:
            from mcp.loader import load_mcp_tools
            async with async_session() as mcp_db:
                mcp_tools = await load_mcp_tools(user_id, user_tier, str(state.get("conversation_id", "")), mcp_db)
        except Exception:
            logger.exception("Failed to load MCP tools")
```

And add `"mcp_tools": mcp_tools` to the return dict.

- [ ] **Step 6: Commit**

```bash
git add backend/core/config.py backend/agent/nodes/agent_loop.py backend/agent/state.py backend/agent/graph.py backend/agent/nodes/router.py
git commit -m "feat(mcp): integrate MCP tools into agent pipeline"
```

---

### Task 5: API Updates — Registry, Tools, Health, Toggle

**Files:**
- Modify: `backend/api/v1/mcp.py`

- [ ] **Step 1: Rewrite MCP API with new endpoints**

```python
# backend/api/v1/mcp.py
"""MCP Gateway API — registry, CRUD, tools discovery, health check."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from db.models import MCPServer
from mcp.loader import invalidate_cache
from mcp.proxy import proxy_discover_tools
from mcp.registry import get_curated_server, get_registry

router = APIRouter()


class MCPServerCreate(BaseModel):
    name: str
    transport: str
    config: dict


class MCPConnectCurated(BaseModel):
    api_key: str


class MCPServerOut(BaseModel):
    id: str
    name: str
    transport: str
    config: dict
    enabled: bool
    curated_id: str | None = None


# --- Registry ---

@router.get("/registry")
async def list_registry():
    """List available curated MCP servers."""
    return get_registry()


# --- CRUD ---

@router.get("/", response_model=list[MCPServerOut])
async def list_servers(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(MCPServer).where(MCPServer.user_id == UUID(user_id)))).scalars().all()
    return [MCPServerOut(
        id=str(r.id), name=r.name, transport=r.transport,
        config={k: v for k, v in (r.config or {}).items() if k != "api_key"},  # hide key
        enabled=r.enabled, curated_id=(r.config or {}).get("curated_id"),
    ) for r in rows]


@router.post("/connect/{curated_id}", response_model=MCPServerOut)
async def connect_curated(
    curated_id: str, body: MCPConnectCurated,
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db),
):
    """Connect a curated MCP server with user's API key."""
    template = get_curated_server(curated_id)
    if not template:
        raise HTTPException(status_code=404, detail="Server not found in registry")

    # Check if already connected
    existing = (await db.execute(
        select(MCPServer).where(MCPServer.user_id == UUID(user_id), MCPServer.name == template["name"])
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Already connected")

    config = {**template["default_config"], "api_key": body.api_key, "curated_id": curated_id}
    srv = MCPServer(user_id=UUID(user_id), name=template["name"], transport=template["transport"], config=config)
    db.add(srv)
    await db.commit()
    await db.refresh(srv)
    await invalidate_cache(user_id)

    return MCPServerOut(
        id=str(srv.id), name=srv.name, transport=srv.transport,
        config={k: v for k, v in config.items() if k != "api_key"},
        enabled=srv.enabled, curated_id=curated_id,
    )


@router.post("/custom", response_model=MCPServerOut)
async def add_custom(body: MCPServerCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    """Add a custom MCP server."""
    srv = MCPServer(user_id=UUID(user_id), name=body.name, transport=body.transport, config=body.config)
    db.add(srv)
    await db.commit()
    await db.refresh(srv)
    await invalidate_cache(user_id)
    return MCPServerOut(id=str(srv.id), name=srv.name, transport=srv.transport, config=srv.config, enabled=srv.enabled)


@router.patch("/{server_id}")
async def toggle_server(server_id: str, enabled: bool, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    srv = await db.get(MCPServer, UUID(server_id))
    if not srv or str(srv.user_id) != user_id:
        raise HTTPException(status_code=404)
    srv.enabled = enabled
    await db.commit()
    await invalidate_cache(user_id)
    return {"ok": True, "enabled": enabled}


@router.delete("/{server_id}")
async def delete_server(server_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    srv = await db.get(MCPServer, UUID(server_id))
    if not srv or str(srv.user_id) != user_id:
        raise HTTPException(status_code=404)
    await db.delete(srv)
    await db.commit()
    await invalidate_cache(user_id)
    return {"ok": True}


# --- Discovery & Health ---

@router.get("/{server_id}/tools")
async def list_tools(server_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    srv = await db.get(MCPServer, UUID(server_id))
    if not srv or str(srv.user_id) != user_id:
        raise HTTPException(status_code=404)
    tools = await proxy_discover_tools(srv)
    return {"tools": tools}


@router.get("/{server_id}/health")
async def health_check(server_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    srv = await db.get(MCPServer, UUID(server_id))
    if not srv or str(srv.user_id) != user_id:
        raise HTTPException(status_code=404)
    try:
        tools = await proxy_discover_tools(srv)
        return {"status": "connected", "tools_count": len(tools)}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

- [ ] **Step 2: Commit**

```bash
git add backend/api/v1/mcp.py
git commit -m "feat(mcp): API — registry, connect curated, tools discovery, health check"
```

---

### Task 6: Frontend — MCP Tab in Settings

**Files:**
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/(app)/settings/page.tsx`

- [ ] **Step 1: Add MCP API methods to api.ts**

Add to `api` object in `frontend/lib/api.ts`:

```typescript
  // MCP Gateway
  mcpRegistry: () => request<Array<{ id: string; name: string; description: string; icon: string; category: string; required_fields: string[] }>>("/mcp/registry"),
  mcpServers: () => request<Array<{ id: string; name: string; transport: string; config: Record<string, unknown>; enabled: boolean; curated_id: string | null }>>("/mcp/"),
  mcpConnect: (curatedId: string, apiKey: string) => request<{ id: string; name: string }>(`/mcp/connect/${curatedId}`, { method: "POST", body: JSON.stringify({ api_key: apiKey }) }),
  mcpAddCustom: (name: string, transport: string, config: Record<string, unknown>) => request<{ id: string }>("/mcp/custom", { method: "POST", body: JSON.stringify({ name, transport, config }) }),
  mcpToggle: (id: string, enabled: boolean) => request<{ ok: boolean }>(`/mcp/${id}?enabled=${enabled}`, { method: "PATCH" }),
  mcpDelete: (id: string) => request<{ ok: boolean }>(`/mcp/${id}`, { method: "DELETE" }),
  mcpTools: (id: string) => request<{ tools: Array<{ name: string; description: string }> }>(`/mcp/${id}/tools`),
  mcpHealth: (id: string) => request<{ status: string; tools_count?: number; error?: string }>(`/mcp/${id}/health`),
```

- [ ] **Step 2: Add MCP tab to settings page**

In `frontend/app/(app)/settings/page.tsx`:

Add "MCP" to tabs array (after "Kết nối"):

```tsx
{ label: "MCP", icon: Wrench },
```

Update imports to add `Plug` icon from lucide-react.

Add MCPTab component and wire it into the tab rendering.

The MCPTab component should:
- Load curated registry + user's connected servers
- Show curated server cards with "Kết nối" button
- API key input modal for connecting
- Connected servers list with toggle + delete
- Connection status indicator (green/red dot)

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/api.ts frontend/app/\(app\)/settings/page.tsx
git commit -m "feat(mcp): frontend MCP tab — registry, connect, toggle, delete"
```

---

### Task 7: Version Bump + Deploy

- [ ] **Step 1: Bump version to 8.0.0**

`backend/pyproject.toml`: `version = "8.0.0"`
`frontend/package.json`: `version: "8.0.0"`

- [ ] **Step 2: Add MCP_GATEWAY_ENABLED to .env.example**

```
MCP_GATEWAY_ENABLED=true
```

- [ ] **Step 3: Commit and deploy**

```bash
git add backend/pyproject.toml frontend/package.json .env.example
git commit -m "feat: V8.0.0 — MCP Gateway Phase 1"
make prod
```

- [ ] **Step 4: Verify**

```bash
curl -s https://jarvis.pmai.space/api/v1/mcp/registry
# Expected: JSON array with 3 curated servers
```

---

### Rollback

```bash
# Disable MCP gateway without redeploying
# Set MCP_GATEWAY_ENABLED=false in .env.prod
# docker compose ... up -d backend
```
