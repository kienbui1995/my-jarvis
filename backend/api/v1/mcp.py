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
from mcp.registry import get_curated_server, get_registry, get_shared_key

router = APIRouter()


class MCPServerCreate(BaseModel):
    name: str
    transport: str
    config: dict


class MCPConnectCurated(BaseModel):
    api_key: str = ""  # Empty = use shared operator key


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
    return get_registry()


# --- CRUD ---

@router.get("/", response_model=list[MCPServerOut])
async def list_servers(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(MCPServer).where(MCPServer.user_id == UUID(user_id)))).scalars().all()
    return [MCPServerOut(
        id=str(r.id), name=r.name, transport=r.transport,
        config={k: v for k, v in (r.config or {}).items() if k != "api_key"},
        enabled=r.enabled, curated_id=(r.config or {}).get("curated_id"),
    ) for r in rows]


@router.post("/connect/{curated_id}", response_model=MCPServerOut)
async def connect_curated(
    curated_id: str, body: MCPConnectCurated,
    user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db),
):
    template = get_curated_server(curated_id)
    if not template:
        raise HTTPException(status_code=404, detail="Server not found in registry")

    existing = (await db.execute(
        select(MCPServer).where(MCPServer.user_id == UUID(user_id), MCPServer.name == template["name"])
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Already connected")

    # Use user's key or fall back to shared operator key
    api_key = body.api_key or get_shared_key(curated_id)
    if not api_key:
        raise HTTPException(status_code=400, detail="API key required (no shared key available)")
    use_shared = not body.api_key and bool(get_shared_key(curated_id))
    config = {**template["default_config"], "api_key": api_key, "curated_id": curated_id, "shared_key": use_shared}
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
    srv = MCPServer(user_id=UUID(user_id), name=body.name, transport=body.transport, config=body.config)
    db.add(srv)
    await db.commit()
    await db.refresh(srv)
    await invalidate_cache(user_id)
    return MCPServerOut(id=str(srv.id), name=srv.name, transport=srv.transport, config=srv.config, enabled=srv.enabled)


@router.patch("/{server_id}")
async def toggle_server(server_id: str, enabled: bool, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(server_id)
    except ValueError:
        raise HTTPException(status_code=404)
    srv = await db.get(MCPServer, uid)
    if not srv or str(srv.user_id) != user_id:
        raise HTTPException(status_code=404)
    srv.enabled = enabled
    await db.commit()
    await invalidate_cache(user_id)
    return {"ok": True, "enabled": enabled}


@router.delete("/{server_id}")
async def delete_server(server_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(server_id)
    except ValueError:
        raise HTTPException(status_code=404)
    srv = await db.get(MCPServer, uid)
    if not srv or str(srv.user_id) != user_id:
        raise HTTPException(status_code=404)
    await db.delete(srv)
    await db.commit()
    await invalidate_cache(user_id)
    return {"ok": True}


# --- Discovery & Health ---

@router.get("/{server_id}/tools")
async def list_tools(server_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(server_id)
    except ValueError:
        raise HTTPException(status_code=404)
    srv = await db.get(MCPServer, uid)
    if not srv or str(srv.user_id) != user_id:
        raise HTTPException(status_code=404)
    tools = await proxy_discover_tools(srv)
    return {"tools": tools}


@router.get("/{server_id}/health")
async def health_check(server_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    try:
        uid = UUID(server_id)
    except ValueError:
        raise HTTPException(status_code=404)
    srv = await db.get(MCPServer, uid)
    if not srv or str(srv.user_id) != user_id:
        raise HTTPException(status_code=404)
    try:
        tools = await proxy_discover_tools(srv)
        return {"status": "connected", "tools_count": len(tools)}
    except Exception as e:
        return {"status": "error", "error": str(e)}
