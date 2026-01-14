from datetime import datetime
from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    BackgroundTasks,
    status,
    Body,
    File,
    Form,
    UploadFile,
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from core.dependencies import get_current_active_user
from database.session import get_database_session
from user_profile.cruds.UserProfileCruds import user_profile_service
from user_profile.cruds.InterestCruds import interest_service
from user_profile.cruds.FollowFollowingCruds import follow_service
from user_profile.request.UpdateProfileRequest import (
    UpdateProfileRequest,
)
from user_profile.request.RespondFollowRequest import RespondFollowRequest
from user_profile.response.ProfileResponse import ProfileResponse
from core.exceptions import (
    BaseCustomException,
    create_http_exception,
    ValidationError,
    InternalServerError,
)
from core.audit import audit_logger
import logging
from user_profile.response.FollowRequestsPaginatedResponse import (
    FollowRequestsPaginatedResponse,
)
from user_profile.response.FollowersPaginatedResponse import FollowersPaginatedResponse
from user_profile.response.FollowingPaginatedResponse import FollowingPaginatedResponse
from user_profile.response.NewFollowersPaginatedResponse import (
    NewFollowersPaginatedResponse,
)
from core.MessageResponse import MessageResponse
from user_profile.response.InterestsResponse import InterestsResponse
from user_profile.request.UserSearchRequest import UserSearchRequest
from user_profile.response.UserSearchResponse import UserSearchResponse
from user_profile.response.TopAccountsResponse import TopAccountsResponse
from sqlalchemy import select
from auth.models.UserProfile import UserProfile
from core.image_utils import ImageUtils

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["User Profile"])


@router.get("/profile", response_model=ProfileResponse, status_code=status.HTTP_200_OK)
async def get_profile(
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        profile = await user_profile_service.get_user_profile(db, current_user)
        return profile
    except BaseCustomException as e:
        logger.warning(f"Profile retrieval failed for user {current_user}: {e.message}")
        raise create_http_exception(e)


@router.get(
    "/profile/{target_user_id}",
    response_model=ProfileResponse,
    status_code=status.HTTP_200_OK,
)
async def get_other_profile(
    target_user_id: str,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        if current_user == target_user_id:
            raise create_http_exception(
                ValidationError("Cannot retrieve your own profile")
            )
        profile = await user_profile_service.get_user_profile(
            db, target_user_id, current_user
        )
        return profile
    except BaseCustomException as e:
        logger.warning(
            f"Profile retrieval failed for user {target_user_id}: {getattr(e, 'message', str(e))}"
        )
        raise create_http_exception(e)


@router.put("/profile", response_model=ProfileResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    background_tasks: BackgroundTasks,
    name: Optional[str] = Form(None),
    bio: Optional[str] = Form(None),
    is_private: Optional[bool] = Form(False),
    interest_ids: Optional[str] = Form(None),
    command_id: Optional[int] = Form(None),
    photo_content_type: Optional[str] = Form(None),
    banner_content_type: Optional[str] = Form(None),
    photo_file: Optional[UploadFile] = File(None),
    banner_file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    photo_bytes = await photo_file.read() if photo_file is not None else None
    banner_bytes = await banner_file.read() if banner_file is not None else None
    if interest_ids is not None:
        interest_ids = [int(i) for i in interest_ids.split(",") if i.strip()]
    else:
        interest_ids = None
    try:
        request_data = UpdateProfileRequest(
            name=name,
            bio=bio,
            is_private=is_private,
            interest_ids=interest_ids,
            command_id=command_id,
            photo_content_type=photo_content_type,
            banner_content_type=banner_content_type,
            photo_bytes=photo_bytes,
            banner_bytes=banner_bytes,
        )
    except Exception as e:
        if e.__class__.__name__ == "ValidationError" and "pydantic" in str(type(e)):
            raise create_http_exception(ValidationError(str(e)))
        raise
    try:
        updated_profile = await user_profile_service.update_user_profile(
            db, current_user, request_data
        )
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "profile_updated",
            current_user,
            client_request.client.host if client_request else "unknown",
        )
        return updated_profile
    except BaseCustomException as e:
        logger.warning(f"Profile update failed for user {current_user}: {e.message}")
        raise create_http_exception(e)


@router.get(
    "/interests/all", response_model=InterestsResponse, status_code=status.HTTP_200_OK
)
async def get_all_interests_route(db: AsyncSession = Depends(get_database_session)):
    try:
        interests = await interest_service.get_all_interests(db)
        return InterestsResponse(interests=interests)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/interests", response_model=InterestsResponse, status_code=status.HTTP_200_OK
)
async def get_interests(
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        interests = await interest_service.get_user_interests(db, current_user)
        return InterestsResponse(interests=interests)
    except BaseCustomException as e:
        logger.warning(
            f"Interest retrieval failed for user {current_user}: {e.message}"
        )
        raise create_http_exception(e)


@router.post(
    "/interests/set", response_model=MessageResponse, status_code=status.HTTP_200_OK
)
async def set_interests(
    background_tasks: BackgroundTasks,
    interest_ids: list[int] = Body(..., embed=True),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    try:
        await interest_service.set_user_interests(db, current_user, interest_ids)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "interests_set",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"interest_ids": interest_ids},
        )
        return MessageResponse(message="Interests set successfully")
    except BaseCustomException as e:
        logger.warning(f"Set interests failed for user {current_user}: {e.message}")
        raise create_http_exception(e)


@router.delete(
    "/interests/remove", response_model=MessageResponse, status_code=status.HTTP_200_OK
)
async def remove_interests(
    background_tasks: BackgroundTasks,
    interest_ids: list[int] = Body(..., embed=True),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    try:
        await interest_service.remove_user_interests(db, current_user, interest_ids)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "interests_removed",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"interest_ids": interest_ids},
        )
        return MessageResponse(message="Interests removed successfully")
    except BaseCustomException as e:
        logger.warning(f"Remove interests failed for user {current_user}: {e.message}")
        raise create_http_exception(e)


@router.post(
    "/follow/{followee_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def follow(
    followee_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    try:
        result = await follow_service.follow_user(db, current_user, followee_id)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "user_followed" if result == "followed" else "follow_requested",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"followee_id": followee_id},
        )
        return MessageResponse(
            message="User followed" if result == "followed" else "Follow request sent"
        )
    except BaseCustomException as e:
        logger.warning(
            f"Follow failed for user {current_user} -> {followee_id}: {getattr(e, 'message', str(e))}"
        )
        raise create_http_exception(e)


@router.put(
    "/follow-request/{follower_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def respond_follow_request_route(
    follower_id: str,
    request: RespondFollowRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    try:
        await follow_service.respond_to_follow_request(
            db, follower_id, current_user, request.accept
        )
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "follow_request_responded",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"follower_id": follower_id, "accepted": request.accept},
        )
        action = "accepted" if request.accept else "declined"
        return MessageResponse(message=f"Follow request {action}")
    except BaseCustomException as e:
        logger.warning(
            f"Respond to follow request failed for {follower_id} -> {current_user}: {getattr(e, 'message', str(e))}"
        )
        raise create_http_exception(e)


@router.delete(
    "/unfollow/{followee_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def unfollow(
    followee_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    try:
        await follow_service.unfollow_user(db, current_user, followee_id)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "user_unfollowed",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"unfollowed_user_id": followee_id},
        )
        return MessageResponse(message="User unfollowed successfully")
    except BaseCustomException as e:
        logger.warning(
            f"Unfollow failed for user {current_user} -> {followee_id}: {e.message}"
        )
        raise create_http_exception(e)


@router.delete(
    "/remove-follower/{follower_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def remove_follower(
    follower_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    """Remove a follower from your follower list. 
    This will prevent them from viewing your content if your account is private,
    and they will need to follow you again to regain access."""
    try:
        await follow_service.remove_follower(db, current_user, follower_id)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "follower_removed",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"removed_follower_id": follower_id},
        )
        return MessageResponse(message="Follower removed successfully")
    except BaseCustomException as e:
        logger.warning(
            f"Remove follower failed for user {current_user} removing {follower_id}: {e.message}"
        )
        raise create_http_exception(e)


@router.get(
    "/follow-requests",
    response_model=FollowRequestsPaginatedResponse,
    status_code=status.HTTP_200_OK,
)
async def get_pending_follow_requests(
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(5, ge=1, le=100),
):
    try:
        requests = await follow_service.get_follow_requests(db, current_user)
        total = len(requests)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = requests[start_idx:end_idx]
        return FollowRequestsPaginatedResponse(
            follow_requests=[
                r.model_dump() if hasattr(r, "model_dump") else r for r in paginated
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
    except BaseCustomException as e:
        logger.warning(
            f"Get follow requests failed for user {current_user}: {getattr(e, 'message', str(e))}"
        )
        raise create_http_exception(e)


@router.get(
    "/followers",
    response_model=FollowersPaginatedResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_followers(
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        followers, total = await follow_service.get_followers(db, current_user, page, page_size)
        return FollowersPaginatedResponse(
            followers=[
                f.model_dump() if hasattr(f, "model_dump") else f for f in followers
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
    except BaseCustomException as e:
        logger.warning(
            f"Get followers failed for user {current_user}: {getattr(e, 'message', str(e))}"
        )
        raise create_http_exception(e)


@router.get(
    "/followers/{target_user_id}",
    response_model=FollowersPaginatedResponse,
    status_code=status.HTTP_200_OK,
)
async def get_other_user_followers(
    target_user_id: str,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        profile = await user_profile_service.get_user_profile(
            db, target_user_id, current_user
        )
        if not (
            not profile.is_private
            or getattr(profile, "is_organizational", False)
            or getattr(profile, "can_view_content", False)
        ):
            return FollowersPaginatedResponse(
                followers=[],
                page=page,
                page_size=page_size,
                total=0,
                message="This account is private. Followers are not visible.",
            )
        followers, total = await follow_service.get_followers(
            db, target_user_id, page, page_size
        )
        return FollowersPaginatedResponse(
            followers=[
                f.model_dump() if hasattr(f, "model_dump") else f for f in followers
            ],
            page=page,
            page_size=page_size,
            total=total,
            message=f"{target_user_id}'s followers",
        )
    except BaseCustomException as e:
        logger.warning(
            f"Get followers failed for user {target_user_id}: {getattr(e, 'message', str(e))}"
        )
        raise create_http_exception(e)


@router.get(
    "/following",
    response_model=FollowingPaginatedResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_following(
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        following, total = await follow_service.get_following(db, current_user, page, page_size)
        return FollowingPaginatedResponse(
            following=[
                f.model_dump() if hasattr(f, "model_dump") else f for f in following
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
    except BaseCustomException as e:
        logger.warning(
            f"Get following failed for user {current_user}: {getattr(e, 'message', str(e))}"
        )
        raise create_http_exception(e)


@router.get(
    "/following/{target_user_id}",
    response_model=FollowingPaginatedResponse,
    status_code=status.HTTP_200_OK,
)
async def get_other_user_following(
    target_user_id: str,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        profile = await user_profile_service.get_user_profile(
            db, target_user_id, current_user
        )
        if not (
            not profile.is_private
            or getattr(profile, "is_organizational", False)
            or getattr(profile, "can_view_content", False)
        ):
            return FollowingPaginatedResponse(
                following=[],
                page=page,
                page_size=page_size,
                total=0,
                message="This account is private. Following list is not visible.",
            )
        following, total = await follow_service.get_following(
            db, target_user_id, page, page_size
        )
        return FollowingPaginatedResponse(
            following=[
                f.model_dump() if hasattr(f, "model_dump") else f for f in following
            ],
            page=page,
            page_size=page_size,
            total=total,
            message=f"{target_user_id} is following",
        )
    except BaseCustomException as e:
        logger.warning(
            f"Get following failed for user {target_user_id}: {getattr(e, 'message', str(e))}"
        )
        raise create_http_exception(e)


@router.get(
    "/new-followers",
    response_model=NewFollowersPaginatedResponse,
    status_code=status.HTTP_200_OK,
)
async def get_new_followers_route(
    since: Optional[datetime] = None,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        new_followers, total = await follow_service.get_new_followers(
            db, current_user, since, page, page_size
        )
        return NewFollowersPaginatedResponse(
            new_followers=[
                f.model_dump() if hasattr(f, "model_dump") else f for f in new_followers
            ],
            page=page,
            page_size=page_size,
            total=total,
        )
    except BaseCustomException as e:
        logger.warning(
            f"Get new followers failed for user {current_user}: {getattr(e, 'message', str(e))}"
        )
        raise create_http_exception(e)


@router.get(
    "/mutual-followers",
    response_model=FollowersPaginatedResponse,
    status_code=status.HTTP_200_OK,
)
async def get_user_mutual_followers(
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        mutuals = await follow_service.get_mutual_followers(db, current_user)
        total = len(mutuals)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated = mutuals[start_idx:end_idx]
        return FollowersPaginatedResponse(
            followers=[
                f.model_dump() if hasattr(f, "model_dump") else f for f in paginated
            ],
            page=page,
            page_size=page_size,
            total=total,
            message="Mutual followers",
        )
    except BaseCustomException as e:
        logger.warning(
            f"Get mutual followers failed for user {current_user}: {getattr(e, 'message', str(e))}"
        )
        raise create_http_exception(e)


@router.post(
    "/users/search", response_model=UserSearchResponse, status_code=status.HTTP_200_OK
)
async def user_search_users(
    request: UserSearchRequest,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await user_profile_service.search_users(db, request)
    except (ValidationError, InternalServerError) as e:
        raise create_http_exception(e)


@router.get(
    "/top-accounts", response_model=TopAccountsResponse, status_code=status.HTTP_200_OK
)
async def get_top_accounts_route(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await user_profile_service.get_top_accounts(db, limit=limit)
    except BaseCustomException as e:
        logger.warning(f"Top accounts retrieval failed: {e.message}")
        raise create_http_exception(e)
