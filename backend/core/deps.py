from typing import AsyncGenerator

from fastapi import Depends
from jose import JWTError, jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.config import settings
from db.session import get_session

security_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator:
    async for session in get_session():
        yield session


async def get_current_user_id(
    cred: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> str:
    try:
        payload = jwt.decode(cred.credentials, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
