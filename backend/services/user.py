"""User service — find or create users from channel identifiers."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User


async def get_or_create_user(
    db: AsyncSession, *, zalo_id: str = "", zalo_bot_id: str = "", telegram_id: str = "", name: str = "",
) -> User | None:
    """Find existing user by channel ID, or create a new one."""
    if zalo_id:
        result = await db.execute(select(User).where(User.zalo_id == zalo_id))
    elif zalo_bot_id:
        result = await db.execute(select(User).where(User.zalo_bot_id == zalo_bot_id))
    elif telegram_id:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    else:
        return None

    user = result.scalar_one_or_none()
    if user:
        # Update name if missing
        if name and not user.name:
            user.name = name
            await db.commit()
        return user

    user = User(
        zalo_id=zalo_id or None, zalo_bot_id=zalo_bot_id or None,
        telegram_id=telegram_id or None, name=name or None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
