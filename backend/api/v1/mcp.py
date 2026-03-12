"""MCP server management — CRUD endpoints for user's MCP servers."""
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from db.models import MCPServer

router = APIRouter()


class MCPServerCreate(BaseModel):
    name: str
    transport: str  # stdio | sse
    config: dict


class MCPServerOut(BaseModel):
    id: str
    name: str
    transport: str
    config: dict
    enabled: bool


@router.get("/", response_model=list[MCPServerOut])
async def list_mcp_servers(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(MCPServer).where(MCPServer.user_id == UUID(user_id)))).scalars().all()
    return [MCPServerOut(id=str(r.id), name=r.name, transport=r.transport, config=r.config, enabled=r.enabled) for r in rows]


@router.post("/", response_model=MCPServerOut)
async def create_mcp_server(body: MCPServerCreate, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    srv = MCPServer(user_id=UUID(user_id), name=body.name, transport=body.transport, config=body.config)
    db.add(srv)
    await db.commit()
    await db.refresh(srv)
    return MCPServerOut(id=str(srv.id), name=srv.name, transport=srv.transport, config=srv.config, enabled=srv.enabled)


@router.delete("/{server_id}")
async def delete_mcp_server(server_id: str, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    srv = await db.get(MCPServer, UUID(server_id))
    if srv and srv.user_id == UUID(user_id):
        await db.delete(srv)
        await db.commit()
    return {"ok": True}
