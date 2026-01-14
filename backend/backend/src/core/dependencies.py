from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_database_session
from caching.cache_service import cache_service
from core.security import verify_token
from core.exceptions import create_http_exception, AuthenticationError, AuthorizationError, NotFoundError
import logging
from sqlalchemy import select
from auth.models.User import User
from datetime import datetime

logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_database_session)
) -> str:
    token = credentials.credentials
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        cached_token = await cache_service.get(f"access_token:{user_id}")
        if not cached_token or cached_token != token:
            raise AuthenticationError("Token not found or expired")
        return user_id
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        if isinstance(e, AuthenticationError):
            raise create_http_exception(e)
        raise AuthenticationError("Could not validate credentials")

async def get_current_active_user(
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
) -> str:
    result = await db.execute(
        select(User).filter(User.user_id == current_user, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found or inactive")
    if user.block_until and user.block_until <= datetime.now().date():
        user.is_blocked = False
        user.block_until = None
        await db.commit()
    if user.is_blocked:
        raise AuthorizationError("Your account has been blocked permanently. Please contact support.")
    if user.block_until and user.block_until > datetime.now().date():
        raise AuthorizationError(f"Your account has been blocked until {user.block_until}. Please contact support.")
    return current_user

async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_database_session)
) -> str:
    token = credentials.credentials
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        is_admin = payload.get("is_admin", False)
        if not user_id or not is_admin:
            raise AuthenticationError("Not an admin user")
        result = await db.execute(select(User).filter(User.user_id == user_id, User.is_active == True, User.is_admin == True))
        user = result.scalar_one_or_none()
        if not user:
            raise AuthenticationError("Admin user not found or inactive")
        if user.block_until and user.block_until <= datetime.now().date():
            user.is_blocked = False
            user.block_until = None
            await db.commit()
        if user.is_blocked or (user.block_until and user.block_until > datetime.now().date()):
            raise AuthenticationError("Admin account is blocked")
        return user_id
    except Exception as e:
        logger.warning(f"Admin authentication failed: {e}")
        raise AuthorizationError("Admin privileges required")
