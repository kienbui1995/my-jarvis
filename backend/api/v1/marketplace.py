"""Plugin marketplace — publish, browse, install custom tools."""
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user_id, get_db
from db.models.system import APIKey, CustomTool
from services.custom_tools import extract_tool_metadata, validate_tool_code

router = APIRouter()


class ToolPublish(BaseModel):
    code: str
    public: bool = False


class ToolInstall(BaseModel):
    tool_id: str


# ── Custom tool CRUD ──

@router.post("/tools")
async def publish_tool(
    body: ToolPublish,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload and validate a custom tool."""
    err = validate_tool_code(body.code)
    if err:
        raise HTTPException(400, err)

    meta = extract_tool_metadata(body.code)
    tool = CustomTool(
        user_id=UUID(user_id),
        name=meta["name"],
        description=meta["description"],
        code=body.code,
        public=body.public,
    )
    db.add(tool)
    await db.commit()
    return {"id": str(tool.id), "name": tool.name, "description": tool.description}


@router.get("/tools")
async def list_marketplace(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List public tools in marketplace."""
    rows = (await db.execute(
        select(CustomTool).where(CustomTool.public.is_(True))
        .order_by(CustomTool.install_count.desc())
        .limit(50)
    )).scalars().all()
    return [
        {
            "id": str(t.id), "name": t.name,
            "description": t.description,
            "installs": t.install_count,
        }
        for t in rows
    ]


@router.get("/tools/mine")
async def list_my_tools(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List user's own custom tools."""
    rows = (await db.execute(
        select(CustomTool).where(CustomTool.user_id == UUID(user_id))
    )).scalars().all()
    return [
        {"id": str(t.id), "name": t.name, "description": t.description,
         "public": t.public, "installs": t.install_count}
        for t in rows
    ]


@router.delete("/tools/{tool_id}")
async def delete_tool(
    tool_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete own custom tool."""
    from sqlalchemy import delete
    await db.execute(
        delete(CustomTool).where(
            CustomTool.id == UUID(tool_id),
            CustomTool.user_id == UUID(user_id),
        )
    )
    await db.commit()
    return {"ok": True}


# ── API key management ──

@router.post("/api-keys")
async def create_api_key(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key for public API access."""
    key = f"jrv_{secrets.token_hex(24)}"
    db.add(APIKey(user_id=UUID(user_id), key=key))
    await db.commit()
    return {"key": key}


@router.get("/api-keys")
async def list_api_keys(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List user's API keys."""
    rows = (await db.execute(
        select(APIKey).where(APIKey.user_id == UUID(user_id))
    )).scalars().all()
    return [
        {"id": str(k.id), "key": k.key[:8] + "...", "name": k.name,
         "active": k.active, "requests": k.request_count}
        for k in rows
    ]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key."""
    key = (await db.execute(
        select(APIKey).where(
            APIKey.id == UUID(key_id), APIKey.user_id == UUID(user_id),
        )
    )).scalar_one_or_none()
    if not key:
        raise HTTPException(404, "API key not found")
    key.active = False
    await db.commit()
    return {"ok": True}
