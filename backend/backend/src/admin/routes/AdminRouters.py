from fastapi import (
    APIRouter,
    Depends,
    status,
    Query,
)
from sqlalchemy.ext.asyncio import AsyncSession
from admin.request.RegisterAdminRequest import RegisterAdminRequest
from admin.request.LoginAdminRequest import LoginAdminRequest
from admin.request.UpdateAdminPasswordRequest import UpdateAdminPasswordRequest
from admin.response.AdminTokenResponse import AdminTokenResponse
from admin.response.AdminResponse import AdminResponse
from admin.cruds.AdminCruds import admin_service
from database.session import get_database_session
from core.dependencies import get_current_admin_user
from admin.request.UserSearchRequest import UserSearchRequest
from admin.response.UserSearchResponse import UserSearchResponse
from admin.request.BlockUserRequest import BlockUserRequest
from admin.request.DeleteUserRequest import DeleteUserRequest
from admin.response.UserTypeStatsResponse import UserTypeStatsResponse
from admin.response.UserActivityStatsResponse import UserActivityStatsResponse
from admin.response.ReportListResponse import ReportListResponse
from core.exceptions import (
    BaseCustomException,
    create_http_exception,
)
from admin.request.UpdateUserStatusRequest import UpdateUserStatusRequest
from admin.response.TweetStatsResponse import TweetStatsResponse
from datetime import datetime
from admin.response.UserDetailsResponse import UserDetailsResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post(
    "/register", response_model=AdminResponse, status_code=status.HTTP_201_CREATED
)
async def register_admin(
    request: RegisterAdminRequest, db: AsyncSession = Depends(get_database_session)
):
    try:
        return await admin_service.register_admin(db, request)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post("/login", response_model=AdminTokenResponse)
async def login_admin(
    request: LoginAdminRequest, db: AsyncSession = Depends(get_database_session)
):
    try:
        return await admin_service.login_admin(db, request)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post("/update-password", response_model=AdminResponse)
async def update_admin_password(
    request: UpdateAdminPasswordRequest,
    db: AsyncSession = Depends(get_database_session),
):
    try:
        return await admin_service.update_admin_password(db, request)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get("/protected", summary="Admin-only protected route")
async def protected_admin_route(current_admin: str = Depends(get_current_admin_user)):
    return {"message": f"Hello, admin {current_admin}! This is a protected route."}


@router.post(
    "/users/search",
    response_model=UserSearchResponse,
    summary="Search and filter users (admin only)",
)
async def admin_search_users(
    request: UserSearchRequest,
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.search_users(db, request)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post("/users/block", summary="Block or unblock a user (admin only)")
async def admin_block_user(
    request: BlockUserRequest,
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.block_user(db, request)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post("/users/delete", summary="Delete a user (admin only)")
async def admin_delete_user(
    request: DeleteUserRequest,
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.delete_user(db, request)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/users/type-stats",
    response_model=UserTypeStatsResponse,
    summary="Get user type stats (admin only)",
)
async def admin_user_type_stats(
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.get_user_type_stats(db)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/users/activity-stats",
    response_model=UserActivityStatsResponse,
    summary="Get user activity stats (admin only)",
)
async def admin_user_activity_stats(
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.get_user_activity_stats(db)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/reports/tweets",
    response_model=ReportListResponse,
    summary="Get paginated tweet reports (admin only)",
)
async def admin_tweet_reports(
    page: int = 1,
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.get_tweet_reports(db, page)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/reports/comments",
    response_model=ReportListResponse,
    summary="Get paginated comment reports (admin only)",
)
async def admin_comment_reports(
    page: int = 1,
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.get_comment_reports(db, page)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post(
    "/users/update-status",
    summary="Update user's prime or organizational status (admin only)",
)
async def admin_update_user_status(
    request: UpdateUserStatusRequest,
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.update_user_status(db, request)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/users/all",
    response_model=UserSearchResponse,
    summary="Get all users paginated (admin only)",
)
async def admin_get_all_users(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.get_all_users_paginated(db, page, page_size)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/blocked-users",
    response_model=UserSearchResponse,
    summary="Get all blocked users paginated (admin only)",
)
async def admin_get_all_blocked_users(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.get_all_blocked_users_paginated(db, page, page_size)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/users/prime",
    response_model=UserSearchResponse,
    summary="Get all prime users (admin only)",
)
async def admin_get_prime_users(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.get_users_by_role(
            db, is_prime=True, page=page, page_size=page_size
        )
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/users/organizational",
    response_model=UserSearchResponse,
    summary="Get all organizational users (admin only)",
)
async def admin_get_organizational_users(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.get_users_by_role(
            db, is_organizational=True, page=page, page_size=page_size
        )
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/users/public",
    response_model=UserSearchResponse,
    summary="Get all public users (admin only)",
)
async def admin_get_public_users(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.get_users_by_role(
            db, is_private=False, page=page, page_size=page_size
        )
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/stats/tweets",
    response_model=TweetStatsResponse,
    summary="Get tweet statistics for a specific date (admin only)",
    description="Retrieve statistics about tweets, likes, comments, shares, bookmarks, and views for a specific date.",
)
async def get_tweet_stats(
    date: datetime = Query(
        ..., description="The date to get statistics for (YYYY-MM-DD)"
    ),
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.get_tweet_stats(db, date)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/users/{user_id}",
    response_model=UserDetailsResponse,
    summary="Get detailed information about a specific user (admin only)",
)
async def admin_get_user_details(
    user_id: str,
    db: AsyncSession = Depends(get_database_session),
    current_admin: str = Depends(get_current_admin_user),
):
    try:
        return await admin_service.get_user_details(db, user_id)
    except BaseCustomException as e:
        raise create_http_exception(e)
