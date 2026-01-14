from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from auth.models.User import User
from auth.models.UserProfile import UserProfile
from auth.models.Token import Token
from auth.models.command import Command
from auth.request.RegisterUserRequest import RegisterRequest
from auth.request.LoginUserRequest import LoginRequest
from auth.request.ForgotPasswordRequest import ForgotPasswordRequest
from auth.response.TokenResponse import TokenResponse
from auth.response.UserResponse import UserResponse
from caching.cache_service import cache_service
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from core.exceptions import (
    ConflictError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    BaseCustomException,
)
from datetime import datetime, timedelta
from core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class AuthService:
    def __init__(self):
        pass

    async def register_user(
        self, db: AsyncSession, request: RegisterRequest
    ) -> TokenResponse:
        result = await db.execute(select(User).filter(User.user_id == request.user_id))
        if result.scalar_one_or_none():
            raise ConflictError("User already exists")
        cmd_result = await db.execute(
            select(Command).where(Command.id == request.command_id)
        )
        command = cmd_result.scalar_one_or_none()
        if not command:
            raise ValidationError("Invalid command ID")
        hashed_password = hash_password(request.password)
        user = User(
            user_id=request.user_id,
            password=hashed_password,
            date_of_birth=request.date_of_birth,
            is_private=True,
            is_active=True,
            command_id=request.command_id,
        )
        db.add(user)
        profile = UserProfile(
            user_id=request.user_id,
            name=request.name,
            is_organizational=False,
            is_prime=False,
        )
        db.add(profile)
        try:
            await db.commit()
            logger.info(
                f"User {request.user_id} registered successfully with command_id {request.command_id}."
            )
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to register user {request.user_id}: {e}")
            raise
        return await self._create_user_tokens(db, request.user_id)

    async def login_user(
        self, db: AsyncSession, request: LoginRequest
    ) -> TokenResponse:
        result = await db.execute(
            select(User).filter(User.user_id == request.user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(request.password, user.password):
            raise AuthenticationError("Invalid credentials")
        if user.block_until and user.block_until <= datetime.now().date():
            user.is_blocked = False
            user.block_until = None
            await db.commit()
        if user.is_blocked:
            raise AuthenticationError(
                "Your account has been blocked permanently. Please contact support."
            )
        if user.block_until and user.block_until > datetime.now().date():
            raise AuthenticationError(
                f"Your account has been blocked until {user.block_until}. Please contact support."
            )
        user.is_online = True
        await db.commit()
        logger.info(f"User {request.user_id} logged in successfully")
        return await self._create_user_tokens(db, user.user_id)

    async def forgot_password(
        self, db: AsyncSession, request: ForgotPasswordRequest
    ) -> None:
        result = await db.execute(select(User).filter(User.user_id == request.user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        if user.date_of_birth != request.date_of_birth:
            raise ValidationError("Invalid date of birth")
        user.password = hash_password(request.new_password)
        try:
            await db.commit()
            logger.info(f"Password reset for user {request.user_id}")
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to reset password for user {request.user_id}: {e}")
            raise
        await self._invalidate_user_tokens(db, request.user_id)

    async def logout_user(self, db: AsyncSession, user_id: str) -> None:
        result = await db.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_online = False
            user.is_active = False
            await db.commit()
        await self._invalidate_user_tokens(db, user_id)
        logger.info(f"User {user_id} logged out successfully")

    async def refresh_token(
        self, db: AsyncSession, refresh_token: str
    ) -> TokenResponse:
        try:
            payload = verify_token(refresh_token)
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid token type")
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid token payload")
            result = await db.execute(
                select(User).filter(User.user_id == user_id, User.is_active == True)
            )
            if not result.scalar_one_or_none():
                raise AuthenticationError("User not found or inactive")
            cached_token = await cache_service.get(f"refresh_token:{user_id}")
            if not cached_token or cached_token != refresh_token:
                raise AuthenticationError("Invalid or expired refresh token")
            return await self._create_user_tokens(db, user_id)
        except BaseCustomException as e:
            logger.error(f"Token refresh failed: {e}")
            raise AuthenticationError("Token refresh failed")

    async def _create_user_tokens(
        self, db: AsyncSession, user_id: str
    ) -> TokenResponse:
        access_token = create_access_token({"sub": user_id})
        refresh_token = create_refresh_token({"sub": user_id})
        access_ttl = settings.ACCESS_TOKEN_EXPIRE_HOURS * 3600
        refresh_ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        await cache_service.set(f"access_token:{user_id}", access_token, access_ttl)
        await cache_service.set(f"refresh_token:{user_id}", refresh_token, refresh_ttl)
        expires_at = datetime.now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        result = await db.execute(select(Token).filter(Token.user_id == user_id))
        token_record = result.scalar_one_or_none()
        if token_record:
            token_record.access_token = access_token
            token_record.refresh_token = refresh_token
            token_record.expires_at = expires_at
        else:
            token_record = Token(
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
            )
            db.add(token_record)
        try:
            await db.commit()
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to store tokens for user {user_id}: {e}")
            raise
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=access_ttl,
        )

    async def _invalidate_user_tokens(self, db: AsyncSession, user_id: str) -> None:
        await cache_service.invalidate_user_tokens(user_id)
        result = await db.execute(select(Token).filter(Token.user_id == user_id))
        token_record = result.scalar_one_or_none()
        if token_record:
            await db.delete(token_record)
            try:
                await db.commit()
            except BaseCustomException as e:
                await db.rollback()
                logger.error(f"Failed to delete token record for user {user_id}: {e}")

    async def get_user_info(self, db: AsyncSession, user_id: str) -> UserResponse:
        result = await db.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        return UserResponse(
            user_id=user.user_id,
            date_of_birth=user.date_of_birth,
            is_private=user.is_private,
            is_active=user.is_active,
            created_at=user.created_at,
            is_online=user.is_online,
        )

    async def change_password(
        self, db: AsyncSession, user_id: str, request
    ) -> TokenResponse:
        result = await db.execute(select(User).filter(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        if not verify_password(request.old_password, user.password):
            raise AuthenticationError("Old password is incorrect")
        user.password = hash_password(request.new_password)
        try:
            await db.commit()
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to change password for user {user_id}: {e}")
            raise
        return await self._create_user_tokens(db, user_id)

    async def set_user_online_status(
        self, db: AsyncSession, user_id: str, is_online: bool
    ) -> None:
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_online = is_online
            await db.commit()


auth_service = AuthService()
