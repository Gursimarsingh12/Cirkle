from fastapi import (
    APIRouter,
    Depends,
    status,
    Request,
    BackgroundTasks,
    Body,
    Query,
    File,
    Form,
    UploadFile,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from core.dependencies import get_current_active_user
from database.session import get_database_session
from core.exceptions import (
    create_http_exception,
    BaseCustomException,
    ValidationError,
)
from tweets.cruds.TweetCruds import tweet_service
from tweets.request.LikeTweetRequest import LikeTweetRequest
from tweets.request.BookmarkTweetRequest import BookmarkTweetRequest
from tweets.request.ShareTweetRequest import ShareTweetRequest
from tweets.request.ReportTweetRequest import ReportTweetRequest
from tweets.request.CommentTweetRequest import CommentTweetRequest
from tweets.request.LikeCommentRequest import LikeCommentRequest
from tweets.request.ReportCommentRequest import ReportCommentRequest
from tweets.response.TweetFeedResponse import TweetFeedResponse
from tweets.response.TweetResponse import TweetResponse, CommentResponse
from tweets.response.CommentsPaginatedResponse import CommentsPaginatedResponse
from tweets.response.ActionResponse import ActionResponse
from tweets.response.SharedTweetResponse import SharedTweetResponse
from caching.celery_worker import (
    refresh_user_feed,
    refresh_user_recommend,
    refresh_followers_feeds,
)
from core.audit import audit_logger
from core.rate_limit import rate_limit
from core.image_utils import ImageUtils
import logging
from auth.models.User import User
from core.exceptions import AuthorizationError
from caching.cache_service import cache_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tweets", tags=["Tweets"])


@router.post(
    "/post",
    response_model=TweetResponse,
    status_code=status.HTTP_201_CREATED,
)
@rate_limit(scope="user")
async def post_tweet_entry(
    background_tasks: BackgroundTasks,
    text: str = Form(..., max_length=500),
    media_files: Optional[list[UploadFile]] = File(
        None, description="Up to 4 media files"
    ),
    media_types: Optional[list[str]] = Form(
        None, description="Media types for each file (image/jpeg, etc.)"
    ),
    client_request: Request = None,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    if media_files and not isinstance(media_files, list):
        media_files = [media_files]

    if isinstance(media_types, str):
        media_types = [mt.strip() for mt in media_types.split(",") if mt.strip()]
    elif (
        isinstance(media_types, list)
        and len(media_types) == 1
        and isinstance(media_types[0], str)
        and "," in media_types[0]
    ):
        media_types = [mt.strip() for mt in media_types[0].split(",") if mt.strip()]

    media = []
    if media_files:
        if len(media_files) > 4:
            raise create_http_exception(
                ValidationError("A tweet can have at most 4 media items.")
            )
        if not media_types or len(media_types) != len(media_files):
            raise create_http_exception(
                ValidationError("media_types must be provided for each media file.")
            )
        for idx, (file, mtype) in enumerate(zip(media_files, media_types)):
            ext = mtype.split("/")[-1]
            file_bytes = await file.read() if file is not None else None
            media_path = ImageUtils.save_tweet_media(
                current_user, "temp", idx + 1, file_bytes, ext
            )
            media.append(
                {
                    "media_type": mtype,
                    "media_path": media_path,
                    "media_bytes": file_bytes,
                }
            )
    request_data = {
        "text": text,
        "media": media,
    }
    try:
        response = await tweet_service.post_tweet(db, current_user, request_data)
        refresh_user_feed.delay(current_user, page=1)
        refresh_user_recommend.delay(current_user, page=1)
        refresh_followers_feeds.delay(current_user, page=1)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "tweet_posted",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"tweet_id": response.id},
        )
        return response
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/feed",
    response_model=TweetFeedResponse,
)
@rate_limit(scope="user")
async def get_feed_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_recommendations: bool = Query(True),
    feed_type: str = Query("latest", regex="^(latest|older)$"),
    last_tweet_id: Optional[int] = Query(None, description="Last tweet ID for infinite scroll"),
    refresh: bool = Query(False, description="Force refresh the feed"),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.get_merged_feed(
            db=db,
            user_id=current_user,
            page=page,
            page_size=page_size,
            include_recommendations=include_recommendations,
            last_tweet_id=last_tweet_id,
            refresh=refresh,
            feed_type=feed_type,
        )
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post(
    "/feed/refresh",
    response_model=TweetFeedResponse,
)
@rate_limit(scope="user")
async def refresh_feed_route(
    page_size: int = Query(20, ge=1, le=100),
    include_recommendations: bool = Query(True),
    force_clear_cache: bool = Query(False, description="Force clear all related caches"),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        if force_clear_cache:
            from caching.cache_service import cache_service
            await cache_service.invalidate_feed_refresh_cache(current_user)
            
        return await tweet_service.get_merged_feed(
            db=db,
            user_id=current_user,
            page=1,
            page_size=page_size,
            include_recommendations=include_recommendations,
            refresh=True,
            feed_type="latest",
        )
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/sent-shares",
    response_model=List[SharedTweetResponse],
    summary="Get tweets shared by the current user",
    description="Get a list of tweets that have been shared by the current user to other users"
)
async def get_sent_shared_tweets_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.get_sent_shared_tweets(db, current_user, page, page_size)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/received-shares",
    response_model=List[SharedTweetResponse],
    summary="Get tweets shared with the current user",
    description="Get a list of tweets that have been shared with the current user by other users"
)
async def get_received_shared_tweets_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.get_received_shared_tweets(db, current_user, page, page_size)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/recommend",
    response_model=TweetFeedResponse,
)
@rate_limit(scope="global")
async def get_recommended_tweets_route(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    page_size: int = Query(20, ge=1, le=100),
    refresh: bool = Query(False, description="Force refresh recommendations"),
):
    try:
        return await tweet_service.get_merged_feed(
            db, current_user, page, page_size, include_recommendations=True, refresh=refresh
        )
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post(
    "/recommend/refresh",
    response_model=TweetFeedResponse,
)
@rate_limit(scope="user")
async def refresh_recommendations_route(
    page_size: int = Query(20, ge=1, le=100),
    force_clear_cache: bool = Query(False, description="Force clear all recommendation caches"),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        if force_clear_cache:
            from caching.cache_service import cache_service
            await cache_service.invalidate_twitter_recommendation_cache()
            await cache_service.invalidate_feed_refresh_cache(current_user)
            
        return await tweet_service.get_merged_feed(
            db=db,
            user_id=current_user,
            page=1,
            page_size=page_size,
            include_recommendations=True,
            refresh=True,
            feed_type="latest",
        )
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/my-tweets",
    response_model=TweetFeedResponse,
)
async def get_my_tweets_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.get_my_tweets(db, current_user, page, page_size)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/liked",
    response_model=TweetFeedResponse,
)
async def get_liked_tweets_route(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.get_liked_tweets(db, current_user, page)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/bookmarked",
    response_model=TweetFeedResponse,
)
async def get_bookmarked_tweets_route(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.get_bookmarked_tweets(db, current_user, page)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/my-comments",
    response_model=List[dict],
)
async def get_my_comments_route(
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.get_my_comments(db, current_user, page)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/{tweet_id}",
    response_model=TweetResponse,
)
async def get_tweet_route(
    tweet_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.get_tweet_response(db, tweet_id, current_user)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post(
    "/like",
    response_model=ActionResponse,
)
@rate_limit()
async def like_tweet_route(
    request: LikeTweetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    try:
        result = await tweet_service.like_tweet(db, current_user, request)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "tweet_liked" if request.like else "tweet_unliked",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"tweet_id": request.tweet_id},
        )
        return result
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post(
    "/bookmark",
    response_model=ActionResponse,
)
@rate_limit()
async def bookmark_tweet_route(
    request: BookmarkTweetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    try:
        result = await tweet_service.bookmark_tweet(db, current_user, request)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "tweet_bookmarked" if request.bookmark else "tweet_unbookmarked",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"tweet_id": request.tweet_id},
        )
        return result
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post(
    "/share",
    response_model=ActionResponse,
)
@rate_limit()
async def share_tweet_route(
    request: ShareTweetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    try:
        result = await tweet_service.share_tweet(db, current_user, request)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "tweet_shared",
            current_user,
            client_request.client.host if client_request else "unknown",
            {
                "tweet_id": request.tweet_id,
                "recipient_ids": request.recipient_ids,
                "recipient_count": len(request.recipient_ids),
                "has_message": bool(request.message),
            },
        )
        return result
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/{tweet_id}/comments",
    response_model=CommentsPaginatedResponse,
)
async def get_comments_route(
    tweet_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        comments, total = await tweet_service.get_comments(db, tweet_id, current_user, page, page_size)
        return CommentsPaginatedResponse(
            comments=comments,
            page=page,
            page_size=page_size,
            total=total
        )
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post(
    "/comment",
    response_model=CommentResponse,
)
@rate_limit()
async def comment_tweet_route(
    request: CommentTweetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    try:
        response = await tweet_service.comment_on_tweet(db, current_user, request)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "tweet_commented",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"tweet_id": request.tweet_id, "comment_id": response.id},
        )
        return response
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post(
    "/comment/like",
    response_model=ActionResponse,
)
@rate_limit()
async def like_comment_route(
    request: LikeCommentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    try:
        result = await tweet_service.like_comment(db, current_user, request)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "comment_liked" if request.like else "comment_unliked",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"comment_id": request.comment_id},
        )
        return result
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post(
    "/report",
    response_model=ActionResponse,
)
@rate_limit()
async def report_tweet_route(
    request: ReportTweetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    try:
        result = await tweet_service.report_tweet(db, current_user, request)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "tweet_reported",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"tweet_id": request.tweet_id},
        )
        return result
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.post(
    "/comment/report",
    response_model=ActionResponse,
)
@rate_limit()
async def report_comment_route(
    request: ReportCommentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
    client_request: Request = None,
):
    try:
        result = await tweet_service.report_comment(db, current_user, request)
        background_tasks.add_task(
            audit_logger.log_auth_event,
            "comment_reported",
            current_user,
            client_request.client.host if client_request else "unknown",
            {"comment_id": request.comment_id},
        )
        return result
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.delete(
    "/{tweet_id}",
    response_model=ActionResponse,
)
async def delete_tweet_route(
    tweet_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.delete_tweet(db, current_user, tweet_id)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.patch(
    "/{tweet_id}",
    response_model=TweetResponse,
    status_code=status.HTTP_200_OK,
    response_description="Tweet updated successfully",
    summary="Edit a tweet",
)
async def edit_tweet_route(
    tweet_id: int,
    background_tasks: BackgroundTasks,
    text: Optional[str] = Form(None),
    existing_media_paths: Optional[List[str]] = Form(
        None, description="Paths of existing images to keep"
    ),
    media_files: Optional[List[UploadFile]] = File(
        None, description="Up to 4 media files"
    ),
    media_types: Optional[List[str]] = Form(
        None, description="Media types for each file (image/jpeg, etc.)"
    ),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    if media_files and not isinstance(media_files, list):
        media_files = [media_files]

    if isinstance(media_types, str):
        media_types = [mt.strip() for mt in media_types.split(",") if mt.strip()]
    elif (
        isinstance(media_types, list)
        and len(media_types) == 1
        and isinstance(media_types[0], str)
        and "," in media_types[0]
    ):
        media_types = [mt.strip() for mt in media_types[0].split(",") if mt.strip()]

    # Build media list for new uploads
    new_media = []
    if media_files:
        if len(media_files) > 4:
            raise create_http_exception(
                ValidationError("A tweet can have at most 4 media items.")
            )
        if not media_types or len(media_types) != len(media_files):
            raise create_http_exception(
                ValidationError("media_types must be provided for each media file.")
            )
        start_index = len(existing_media_paths or [])
        for idx, (file, mtype) in enumerate(zip(media_files, media_types)):
            ext = mtype.split("/")[-1]
            file_bytes = await file.read() if file is not None else None
            media_path = ImageUtils.save_tweet_media(
                current_user, tweet_id, start_index + idx + 1, file_bytes, ext
            )
            new_media.append(
                {
                    "media_type": mtype,
                    "media_path": media_path,
                    "media_bytes": file_bytes,
                }
            )

    # Combine existing and new media
    final_media = []
    if existing_media_paths:
        for path in existing_media_paths:
            final_media.append({"media_path": path, "existing": True})
    final_media.extend(new_media)

    if len(final_media) > 4:
        raise create_http_exception(
            ValidationError("A tweet can have at most 4 media items.")
        )

    try:
        return await tweet_service.edit_tweet(
            db, current_user, tweet_id, text, final_media
        )
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.patch(
    "/comment/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
    response_description="Comment updated successfully",
    summary="Edit a comment",
)
async def edit_comment_route(
    comment_id: int,
    text: str = Body(...),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.edit_comment(db, current_user, comment_id, text)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/comment/{comment_id}/replies",
    response_model=List[CommentResponse],
)
async def get_comment_replies_route(
    comment_id: int,
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.get_comment_replies(
            db, comment_id, current_user, page
        )
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.delete(
    "/comment/{comment_id}",
    response_model=ActionResponse,
)
async def delete_comment_route(
    comment_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.delete_comment(db, current_user, comment_id)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/{tweet_id}/comments/all",
    response_model=List[CommentResponse],
)
async def get_all_comments_flat_route(
    tweet_id: int,
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.get_all_comments_flat(db, tweet_id, current_user)
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/user/{user_id}/tweets",
    response_model=TweetFeedResponse,
)
async def get_user_tweets_route(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    try:
        return await tweet_service.get_user_tweets(
            db, user_id, page, page_size, requester_id=current_user
        )
    except BaseCustomException as e:
        raise create_http_exception(e)


@router.get(
    "/mutual-followers",
    response_model=List[str],
)
async def get_mutual_followers_for_sharing_route(
    candidate_user_ids: str = Query(None, description="Optional comma-separated list of user IDs to check mutual follow relationship with"),
    db: AsyncSession = Depends(get_database_session),
    current_user: str = Depends(get_current_active_user),
):
    """Get mutual followers for the current user - useful for tweet sharing"""
    try:
        candidate_ids_list = None
        if candidate_user_ids:
            candidate_ids_list = [uid.strip() for uid in candidate_user_ids.split(",") if uid.strip()]
            
        mutual_followers = await tweet_service.get_mutual_followers_for_user(
            db, current_user, candidate_user_ids=candidate_ids_list
        )
        return mutual_followers
    except BaseCustomException as e:
        raise create_http_exception(e)


# Cache monitoring endpoints for administrators
@router.get(
    "/admin/cache/health",
    response_model=dict,
    summary="Get cache health metrics",
    description="Get detailed cache health and performance metrics (Admin only)"
)
async def get_cache_health_route(
    current_user: str = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session),
):
    """Get cache health metrics (Admin only)"""
    try:
        # Verify admin access
        user = await db.execute(select(User).where(User.user_id == current_user))
        user_obj = user.scalar_one_or_none()
        if not user_obj or not user_obj.is_admin:
            raise AuthorizationError("Admin access required")
        
        health_data = await cache_service.get_cache_health()
        return health_data
    except BaseCustomException as e:
        raise create_http_exception(e)

@router.get(
    "/admin/cache/metrics",
    response_model=dict,
    summary="Get cache metrics",
    description="Get detailed cache operation metrics (Admin only)"
)
async def get_cache_metrics_route(
    current_user: str = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session),
):
    """Get cache metrics (Admin only)"""
    try:
        # Verify admin access
        user = await db.execute(select(User).where(User.user_id == current_user))
        user_obj = user.scalar_one_or_none()
        if not user_obj or not user_obj.is_admin:
            raise AuthorizationError("Admin access required")
        
        metrics = await cache_service.get_metrics()
        return {
            "status": "success",
            "metrics": metrics,
            "recommendations": []
        }
    except BaseCustomException as e:
        raise create_http_exception(e)

@router.post(
    "/admin/cache/metrics/reset",
    response_model=dict,
    summary="Reset cache metrics",
    description="Reset cache operation metrics (Admin only)"
)
async def reset_cache_metrics_route(
    current_user: str = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session),
):
    """Reset cache metrics (Admin only)"""
    try:
        # Verify admin access
        user = await db.execute(select(User).where(User.user_id == current_user))
        user_obj = user.scalar_one_or_none()
        if not user_obj or not user_obj.is_admin:
            raise AuthorizationError("Admin access required")
        
        success = await cache_service.reset_metrics()
        return {
            "status": "success" if success else "error",
            "message": "Cache metrics reset successfully" if success else "Failed to reset cache metrics"
        }
    except BaseCustomException as e:
        raise create_http_exception(e)

@router.get(
    "/admin/cache/info/{pattern}",
    response_model=dict,
    summary="Get cache key information",
    description="Get information about cached keys matching a pattern (Admin only)"
)
async def get_cache_info_route(
    pattern: str,
    current_user: str = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session),
):
    """Get cache key information by pattern (Admin only)"""
    try:
        # Verify admin access
        user = await db.execute(select(User).where(User.user_id == current_user))
        user_obj = user.scalar_one_or_none()
        if not user_obj or not user_obj.is_admin:
            raise AuthorizationError("Admin access required")
        
        # Validate pattern to prevent abuse
        if len(pattern) < 2:
            raise ValidationError("Pattern must be at least 2 characters")
        
        info = await cache_service.cache_info(pattern)
        return info
    except BaseCustomException as e:
        raise create_http_exception(e)
