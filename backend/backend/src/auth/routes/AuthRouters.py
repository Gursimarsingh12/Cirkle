from fastapi import APIRouter, Depends, status, Request, BackgroundTasks, Body
from sqlalchemy.ext.asyncio import AsyncSession
from core.rate_limit import rate_limit
from core.MessageResponse import MessageResponse
from database.session import get_database_session
from auth.request.RegisterUserRequest import RegisterRequest
from auth.request.LoginUserRequest import LoginRequest
from auth.request.ForgotPasswordRequest import ForgotPasswordRequest
from auth.cruds.AuthCruds import auth_service
from auth.response.TokenResponse import TokenResponse
from auth.request.RefreshTokenRequest import RefreshTokenRequest
from auth.response.UserResponse import UserResponse
from core.dependencies import get_current_active_user
from core.exceptions import create_http_exception, BaseCustomException
from core.audit import audit_logger
import logging
from auth.cruds.CommandCruds import command_service
from auth.response.CommandResponse import CommandResponse
from auth.request.ChangePasswordRequest import ChangePasswordRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=5)
async def register(
    request: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    client_request: Request = None
):
    try:
        result = await auth_service.register_user(db, request)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "user_registered",
            request.user_id,
            client_request.client.host if client_request else "unknown"
        )
        logger.info(f"User {request.user_id} registered successfully")
        return result
    except BaseCustomException as e:
        logger.warning(f"Registration failed for user {request.user_id}: {e.message}")
        raise create_http_exception(e)

@router.post("/login", response_model=TokenResponse)
@rate_limit(requests_per_minute=10)
async def login(
    request: LoginRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    client_request: Request = None
):
    try:
        result = await auth_service.login_user(db, request)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "user_login_success",
            request.user_id,
            client_request.client.host if client_request else "unknown"
        )
        return result
    except BaseCustomException as e:
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "user_login_failed",
            request.user_id,
            client_request.client.host if client_request else "unknown",
            {"error": e.message}
        )
        logger.warning(f"Login failed for user {request.user_id}: {e.message}")
        raise create_http_exception(e)

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
@rate_limit(requests_per_minute=3)
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    client_request: Request = None
):
    try:
        await auth_service.forgot_password(db, request)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "password_reset_success",
            request.user_id,
            client_request.client.host if client_request else "unknown"
        )
        return MessageResponse(message="Password reset successfully")
    except BaseCustomException as e:
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "password_reset_failed",
            request.user_id,
            client_request.client.host if client_request else "unknown",
            {"error": e.message}
        )
        logger.warning(f"Password reset failed for user {request.user_id}: {e.message}")
        raise create_http_exception(e)

@router.post("/refresh", response_model=TokenResponse)
@rate_limit(requests_per_minute=20)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_database_session)
):
    try:
        return await auth_service.refresh_token(db, request.refresh_token)
    except BaseCustomException as e:
        logger.warning(f"Token refresh failed: {e.message}")
        raise create_http_exception(e)

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    background_tasks: BackgroundTasks,
    current_user: str = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session),
    client_request: Request = None
):
    try:
        await auth_service.logout_user(db, current_user)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "user_logout",
            current_user,
            client_request.client.host if client_request else "unknown"
        )
        return MessageResponse(message="Logged out successfully")
    except BaseCustomException as e:
        logger.error(f"Logout failed for user {current_user}: {e.message}")
        raise create_http_exception(e)

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: str = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    try:
        return await auth_service.get_user_info(db, current_user)
    except BaseCustomException as e:
        logger.error(f"Failed to get user info for {current_user}: {e.message}")
        raise create_http_exception(e)

@router.get("/commands", response_model=list[CommandResponse], status_code=status.HTTP_200_OK)
async def get_commands(db: AsyncSession = Depends(get_database_session)):
    commands = await command_service.get_all_commands(db)
    return [CommandResponse(id=cmd.id, name=cmd.name) for cmd in commands]

@router.post("/change-password", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user)
):
    try:
        return await auth_service.change_password(db, current_user, request)
    except BaseCustomException as e:
        logger.warning(f"Password change failed for user {current_user}: {e.message}")
        raise create_http_exception(e)

@router.post("/set-online-status", status_code=status.HTTP_200_OK)
async def set_online_status(
    is_online: bool = Body(..., embed=True),
    current_user: str = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
):
    try:
        await auth_service.set_user_online_status(db, current_user, is_online)
        return MessageResponse(message=f"Online status set to {is_online}")
    except BaseCustomException as e:
        raise create_http_exception(e)