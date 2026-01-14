from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from auth.models.User import User
from admin.request.RegisterAdminRequest import RegisterAdminRequest
from admin.request.LoginAdminRequest import LoginAdminRequest
from admin.request.UpdateAdminPasswordRequest import UpdateAdminPasswordRequest
from admin.response.AdminTokenResponse import AdminTokenResponse
from admin.response.AdminResponse import AdminResponse
from auth.models.command import Command
from user_profile.models.Interest import Interest
from core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from core.exceptions import (
    ConflictError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    InternalServerError,
    BaseCustomException,
)
from datetime import datetime, timedelta
import logging
from admin.request.UserSearchRequest import UserSearchRequest
from admin.response.UserSearchResponse import UserSearchResponse
from auth.models.UserProfile import UserProfile
from sqlalchemy import or_, and_
from admin.request.BlockUserRequest import BlockUserRequest
from admin.request.DeleteUserRequest import DeleteUserRequest
from admin.response.UserTypeStatsResponse import UserTypeStatsResponse
from admin.response.UserActivityStatsResponse import UserActivityStatsResponse
from admin.response.ReportListResponse import ReportListResponse
from tweets.models.TweetReport import TweetReport
from tweets.models.CommentReport import CommentReport
from caching.cache_service import cache_service
from user_profile.models.UserInterest import UserInterest
from tweets.models.TweetMedia import TweetMedia
from tweets.models.Tweet import Tweet
from tweets.models.Comment import Comment
from tweets.models.TweetLike import TweetLike
from tweets.models.CommentLike import CommentLike
from tweets.models.Bookmark import Bookmark
from tweets.models.Share import Share
from tweets.models.TweetReport import TweetReport
from tweets.models.CommentReport import CommentReport
from user_profile.models.Follower import Follower
from user_profile.models.FollowRequest import FollowRequest
from auth.models.UserProfile import UserProfile
from user_profile.models.UserInterest import UserInterest
from tweets.models.TweetMedia import TweetMedia
from admin.request.UpdateUserStatusRequest import UpdateUserStatusRequest
from dateutil.relativedelta import relativedelta
from typing import Optional
from admin.response.TweetStatsResponse import TweetStatsResponse
from admin.response.UserDetailsResponse import UserDetailsResponse
from sqlalchemy.exc import SQLAlchemyError
from core.image_utils import ImageUtils
from sqlalchemy.orm import aliased
import json

logger = logging.getLogger(__name__)


class AdminCruds:
    async def register_admin(
        self, db: AsyncSession, request: RegisterAdminRequest
    ) -> AdminResponse:
        result = await db.execute(select(User).filter(User.user_id == request.user_id))
        user = result.scalar_one_or_none()
        if user:
            raise ConflictError("User ID already exists")
        new_user = User(
            user_id=request.user_id,
            password=hash_password(request.password),
            date_of_birth=datetime.now(),
            is_admin=True,
            is_active=True,
            is_blocked=False,
            block_until=None,
            is_private=True,
            command_id=1,
        )
        db.add(new_user)
        await db.commit()
        await cache_service.invalidate_admin_cache()
        return AdminResponse(user_id=new_user.user_id, is_admin=new_user.is_admin)

    async def login_admin(
        self, db: AsyncSession, request: LoginAdminRequest
    ) -> AdminTokenResponse:
        result = await db.execute(
            select(User).filter(
                User.user_id == request.user_id,
                User.is_admin == True,
                User.is_active == True,
            )
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(request.password, user.password):
            raise AuthenticationError("Invalid credentials or not an admin")
        if user.is_blocked or (
            user.block_until and user.block_until > datetime.now().date()
        ):
            raise AuthenticationError("Admin account is blocked")
        access_token = create_access_token({"sub": user.user_id, "is_admin": True})
        refresh_token = create_refresh_token({"sub": user.user_id, "is_admin": True})
        return AdminTokenResponse(
            access_token=access_token, refresh_token=refresh_token
        )

    async def update_admin_password(
        self, db: AsyncSession, request: UpdateAdminPasswordRequest
    ) -> AdminResponse:
        result = await db.execute(
            select(User).filter(User.user_id == request.user_id, User.is_admin == True)
        )
        user = result.scalar_one_or_none()
        if not user or not verify_password(request.old_password, user.password):
            raise AuthenticationError("Invalid credentials or not an admin")
        user.password = hash_password(request.new_password)
        await db.commit()
        await cache_service.invalidate_user_tokens(user.user_id)
        await cache_service.invalidate_user_admin_cache(user.user_id)
        return AdminResponse(user_id=user.user_id, is_admin=user.is_admin)

    async def search_users(
        self, db: AsyncSession, request: UserSearchRequest
    ) -> UserSearchResponse:
        cache_key = f"admin_search_users:p{request.page}:s{request.search or 'none'}:c{request.command_id or 'all'}:o{request.is_organizational}:pr{request.is_prime}:pv{request.is_private}"
        cached = await cache_service.get(cache_key)
        if cached:
            logger.info(f"Cache hit for admin user search: {cache_key}")
            return UserSearchResponse(**cached)
        logger.info(f"Cache miss for admin user search: {cache_key}")
        page_size = 20
        offset = (request.page - 1) * page_size
        try:
            filters = [User.is_admin == False]
            if request.search:
                search_term = f"%{request.search}%"
                filters.append(
                    or_(
                        User.user_id.ilike(search_term),
                        UserProfile.name.ilike(search_term),
                    )
                )
            if request.command_id is not None:
                filters.append(UserProfile.command_id == request.command_id)
            if request.is_organizational is not None:
                filters.append(
                    UserProfile.is_organizational == request.is_organizational
                )
            if request.is_private is not None:
                filters.append(User.is_private == request.is_private)
            if request.is_prime is not None:
                filters.append(UserProfile.is_prime == request.is_prime)
            count_query = (
                select(func.count(User.user_id))
                .select_from(User)
                .join(UserProfile, User.user_id == UserProfile.user_id)
                .where(and_(*filters))
            )
            total_count = (await db.execute(count_query)).scalar_one()
            if total_count == 0:
                empty_response = UserSearchResponse(
                    users=[], total=0, page=request.page, page_size=page_size
                )
                await cache_service.set(cache_key, empty_response.model_dump(), ttl=300)
                return empty_response
            query = (
                select(User, UserProfile)
                .join(UserProfile, User.user_id == UserProfile.user_id)
                .where(and_(*filters))
                .order_by(User.user_id)
                .offset(offset)
                .limit(page_size)
            )
            result = (await db.execute(query)).all()
            users = []
            for user, profile in result:
                users.append(
                    {
                        "user_id": user.user_id,
                        "name": profile.name,
                        "is_organizational": profile.is_organizational,
                        "is_private": user.is_private,
                        "is_prime": profile.is_prime,
                        "command_id": profile.command_id,
                        "is_blocked": user.is_blocked,
                    }
                )
            response = UserSearchResponse(
                users=users, total=total_count, page=request.page, page_size=page_size
            )
            cache_ttl = 600 if request.search else 1800
            await cache_service.set(cache_key, response.model_dump(), ttl=cache_ttl)
            return response
        except BaseCustomException as e:
            raise e

    async def block_user(self, db: AsyncSession, request: BlockUserRequest) -> dict:
        result = await db.execute(
            select(User).filter(User.user_id == request.user_id, User.is_admin == False)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        if request.block_type == "permanent":
            user.is_blocked = True
            user.block_until = None
        elif request.block_type == "week":
            user.is_blocked = True
            user.block_until = datetime.now().date() + timedelta(weeks=1)
        elif request.block_type == "month":
            user.is_blocked = True
            user.block_until = datetime.now().date() + relativedelta(months=1)
        elif request.block_type == "custom" and request.custom_until:
            user.is_blocked = True
            if isinstance(request.custom_until, str):
                user.block_until = datetime.strptime(
                    request.custom_until, "%Y-%m-%d"
                ).date()
            else:
                user.block_until = request.custom_until
        elif request.block_type == "unblock":
            user.is_blocked = False
            user.block_until = None
        else:
            raise ValidationError("Invalid block_type or missing custom_until")
        await db.commit()
        await cache_service.invalidate_user_cache(request.user_id)
        await cache_service.invalidate_admin_cache()
        return {
            "success": True,
            "message": f"User {request.user_id} block status updated",
        }

    async def _get_all_descendants_flat(self, db, parent_ids):
        all_ids = set()
        queue = list(parent_ids)
        while queue:
            child_ids_result = await db.execute(
                select(Comment.id).where(Comment.parent_comment_id.in_(queue))
            )
            child_ids = [row[0] for row in child_ids_result.all()]
            new_child_ids = [cid for cid in child_ids if cid not in all_ids]
            all_ids.update(new_child_ids)
            queue = new_child_ids
        return list(all_ids)[::-1] + list(parent_ids)

    async def delete_user(self, db: AsyncSession, request: DeleteUserRequest) -> dict:
        result = await db.execute(
            select(User).filter(User.user_id == request.user_id, User.is_admin == False)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        await db.execute(
            TweetLike.__table__.delete().where(TweetLike.user_id == request.user_id)
        )
        await db.execute(
            CommentLike.__table__.delete().where(CommentLike.user_id == request.user_id)
        )
        await db.execute(
            Bookmark.__table__.delete().where(Bookmark.user_id == request.user_id)
        )
        await db.execute(
            Share.__table__.delete().where(Share.user_id == request.user_id)
        )
        await db.execute(
            Share.__table__.delete().where(Share.recipient_id == request.user_id)
        )
        await db.execute(
            Follower.__table__.delete().where(Follower.follower_id == request.user_id)
        )
        await db.execute(
            Follower.__table__.delete().where(Follower.followee_id == request.user_id)
        )
        await db.execute(
            FollowRequest.__table__.delete().where(
                FollowRequest.follower_id == request.user_id
            )
        )
        await db.execute(
            FollowRequest.__table__.delete().where(
                FollowRequest.followee_id == request.user_id
            )
        )
        await db.execute(
            TweetReport.__table__.delete().where(TweetReport.user_id == request.user_id)
        )
        await db.execute(
            CommentReport.__table__.delete().where(
                CommentReport.user_id == request.user_id
            )
        )
        await db.execute(
            Comment.__table__.delete().where(Comment.user_id == request.user_id)
        )
        await db.execute(
            Tweet.__table__.delete().where(Tweet.user_id == request.user_id)
        )
        await db.execute(
            UserProfile.__table__.delete().where(UserProfile.user_id == request.user_id)
        )
        await db.execute(
            UserInterest.__table__.delete().where(
                UserInterest.user_id == request.user_id
            )
        )
        tweet_ids = [
            row[0]
            for row in (
                await db.execute(
                    Tweet.__table__.select()
                    .with_only_columns(Tweet.id)
                    .where(Tweet.user_id == request.user_id)
                )
            ).all()
        ]
        if tweet_ids:
            await db.execute(
                TweetMedia.__table__.delete().where(TweetMedia.tweet_id.in_(tweet_ids))
            )
        await db.delete(user)
        await db.commit()
        await cache_service.invalidate_user_cache(request.user_id)
        await cache_service.invalidate_profile_cache(request.user_id)
        await cache_service.invalidate_user_tokens(request.user_id)
        await cache_service.invalidate_interests_cache(request.user_id)
        await cache_service.invalidate_follow_cache(follower_id=request.user_id)
        await cache_service.invalidate_follow_cache(followee_id=request.user_id)
        await cache_service.invalidate_tweet_feed_cache(request.user_id)
        await cache_service.invalidate_admin_cache()
        return {"success": True, "message": f"User {request.user_id} deleted"}

    async def get_user_type_stats(self, db: AsyncSession) -> UserTypeStatsResponse:
        cache_key = "admin_user_type_stats"
        cached = await cache_service.get(cache_key)
        if cached:
            logger.info("Cache hit for admin user type stats")
            return UserTypeStatsResponse(**cached)
        logger.info("Cache miss for admin user type stats")
        try:
            stats_query = (
                select(
                    func.count(UserProfile.user_id).label("total_users"),
                    func.sum(case((UserProfile.is_prime == True, 1), else_=0)).label(
                        "total_prime"
                    ),
                    func.sum(
                        case((UserProfile.is_organizational == True, 1), else_=0)
                    ).label("total_organizational"),
                    func.sum(case((User.is_private == True, 1), else_=0)).label(
                        "total_private"
                    ),
                    func.sum(case((User.is_private == False, 1), else_=0)).label(
                        "total_public"
                    ),
                )
                .select_from(UserProfile)
                .join(User, UserProfile.user_id == User.user_id)
                .where(User.is_admin == False)
            )
            result = (await db.execute(stats_query)).first()
            response = UserTypeStatsResponse(
                total_users=result.total_users or 0,
                total_prime=result.total_prime or 0,
                total_organizational=result.total_organizational or 0,
                total_private=result.total_private or 0,
                total_public=result.total_public or 0,
            )
            await cache_service.set(cache_key, response.model_dump(), ttl=600)
            return response
        except BaseCustomException as e:
            raise e

    async def get_user_activity_stats(
        self, db: AsyncSession
    ) -> UserActivityStatsResponse:
        cache_key = "admin_user_activity_stats"
        cached = await cache_service.get(cache_key)
        if cached:
            logger.info("Cache hit for admin user activity stats")
            return UserActivityStatsResponse(**cached)
        logger.info("Cache miss for admin user activity stats")
        try:
            activity_query = (
                select(
                    func.count(UserProfile.user_id).label("total_users"),
                    func.sum(case((User.is_active == True, 1), else_=0)).label(
                        "active_users"
                    ),
                    func.sum(case((User.is_online == True, 1), else_=0)).label(
                        "online_users"
                    ),
                )
                .select_from(UserProfile)
                .join(User, UserProfile.user_id == User.user_id)
                .where(User.is_admin == False)
            )
            result = (await db.execute(activity_query)).first()
            response = UserActivityStatsResponse(
                total_users=result.total_users or 0,
                active_users=result.active_users or 0,
                online_users=result.online_users or 0,
            )
            await cache_service.set(cache_key, response.model_dump(), ttl=300)
            return response
        except BaseCustomException as e:
            raise e

    async def get_tweet_reports(
        self, db: AsyncSession, page: int = 1
    ) -> ReportListResponse:
        cache_key = f"admin_tweet_reports:p{page}"
        cached = await cache_service.get(cache_key)
        if cached:
            logger.info(f"Cache hit for admin tweet reports page {page}")
            return ReportListResponse(**cached)
        logger.info(f"Cache miss for admin tweet reports page {page}")
        page_size = 20
        offset = (page - 1) * page_size
        try:
            total_query = select(func.count(func.distinct(TweetReport.tweet_id)))
            total_count = (await db.execute(total_query)).scalar_one()
            if total_count == 0:
                empty_response = ReportListResponse(
                    reports=[], total=0, page=page, page_size=page_size
                )
                await cache_service.set(cache_key, empty_response.model_dump(), ttl=300)
                return empty_response
            TweetAuthorProfile = aliased(UserProfile, name="tweet_author_profile")
            reports_query = (
                select(
                    TweetReport.tweet_id,
                    func.count(TweetReport.id).label("report_count"),
                    func.json_arrayagg(
                        func.json_object(
                            "report_id",
                            TweetReport.id,
                            "reporter_id",
                            TweetReport.user_id,
                            "reporter_name",
                            UserProfile.name,
                            "reason",
                            TweetReport.reason,
                            "created_at",
                            TweetReport.created_at,
                        )
                    ).label("reporters"),
                    func.max(TweetReport.created_at).label("latest_report_time"),
                    func.min(TweetReport.created_at).label("first_report_time"),
                    Tweet.text.label("tweet_text"),
                    TweetAuthorProfile.name.label("tweet_author_name"),
                )
                .join(UserProfile, TweetReport.user_id == UserProfile.user_id)
                .outerjoin(Tweet, TweetReport.tweet_id == Tweet.id)
                .outerjoin(
                    TweetAuthorProfile, Tweet.user_id == TweetAuthorProfile.user_id
                )
                .group_by(TweetReport.tweet_id, Tweet.text, TweetAuthorProfile.name)
                .order_by(func.max(TweetReport.created_at).desc())
                .offset(offset)
                .limit(page_size)
            )
            paginated_reports = (await db.execute(reports_query)).all()
            report_list = []
            for row in paginated_reports:
                (
                    tweet_id,
                    report_count,
                    reporters_data,
                    latest_time,
                    first_time,
                    tweet_text,
                    tweet_author_name,
                ) = row
                if reporters_data:
                    try:
                        reporters_data_parsed = json.loads(reporters_data)
                    except Exception:
                        reporters_data_parsed = []
                else:
                    reporters_data_parsed = []
                snapshot_result = await db.execute(
                    select(TweetReport.snapshot)
                    .where(TweetReport.tweet_id == tweet_id)
                    .order_by(TweetReport.created_at.desc())
                    .limit(1)
                )
                snapshot = snapshot_result.scalar_one_or_none()
                
                # Enhance snapshot with media_path if missing
                enhanced_snapshot = None
                has_media = False
                if snapshot:
                    enhanced_snapshot = snapshot.copy() if isinstance(snapshot, dict) else snapshot
                    if isinstance(enhanced_snapshot, dict) and "media" in enhanced_snapshot:
                        has_media = len(enhanced_snapshot["media"]) > 0
                        if has_media:
                            for media_item in enhanced_snapshot["media"]:
                                if "media_path" not in media_item:
                                    # Fetch media_path from database for legacy snapshots
                                    media_query = await db.execute(
                                        select(TweetMedia.media_path, TweetMedia.media_type)
                                        .where(
                                            TweetMedia.tweet_id == tweet_id,
                                            TweetMedia.media_type == media_item.get("media_type")
                                        )
                                        .limit(1)
                                    )
                                    media_result = media_query.first()
                                    if media_result:
                                        media_item["media_path"] = media_result.media_path
                else:
                    # If no snapshot exists, create a minimal one with current tweet media
                    enhanced_snapshot = {"media": []}
                    media_query = await db.execute(
                        select(TweetMedia.media_path, TweetMedia.media_type)
                        .where(TweetMedia.tweet_id == tweet_id)
                    )
                    media_results = media_query.fetchall()
                    if media_results:
                        has_media = True
                        enhanced_snapshot["media"] = [
                            {
                                "media_type": media.media_type,
                                "media_path": media.media_path
                            }
                            for media in media_results
                        ]
                
                if not tweet_text:
                    tweet_text = "Tweet not found or deleted"
                elif len(tweet_text) > 100:
                    tweet_text = tweet_text[:100] + "..."
                if not tweet_author_name:
                    tweet_author_name = "Unknown User"
                    
                report_list.append(
                    {
                        "tweet_id": tweet_id,
                        "tweet_text": tweet_text,
                        "tweet_author_name": tweet_author_name,
                        "report_count": report_count,
                        "reporters": reporters_data_parsed,
                        "reporter_count": len(reporters_data_parsed),
                        "first_reported_at": first_time,
                        "latest_reported_at": latest_time,
                        "latest_snapshot": enhanced_snapshot,
                        "has_media": has_media,
                        "reasons_summary": (
                            list(set([r["reason"] for r in reporters_data_parsed]))
                            if reporters_data_parsed
                            else []
                        ),
                    }
                )
            response = ReportListResponse(
                reports=report_list, total=total_count, page=page, page_size=page_size
            )
            await cache_service.set(cache_key, response.model_dump(), ttl=300)
            return response
        except BaseCustomException as e:
            raise e

    async def get_comment_reports(
        self, db: AsyncSession, page: int = 1
    ) -> ReportListResponse:
        page_size = 20
        report_query = (
            select(
                CommentReport.comment_id,
                func.count(CommentReport.id).label("report_count"),
                func.json_arrayagg(
                    func.json_object(
                        "report_id",
                        CommentReport.id,
                        "reporter_id",
                        CommentReport.user_id,
                        "reporter_name",
                        UserProfile.name,
                        "reason",
                        CommentReport.reason,
                        "created_at",
                        CommentReport.created_at,
                    )
                ).label("reporters"),
                func.max(CommentReport.created_at).label("latest_report_time"),
                func.min(CommentReport.created_at).label("first_report_time"),
            )
            .join(UserProfile, CommentReport.user_id == UserProfile.user_id)
            .group_by(CommentReport.comment_id)
            .order_by(func.max(CommentReport.created_at).desc())
        )
        total_query = select(func.count()).select_from(
            select(CommentReport.comment_id).distinct().subquery()
        )
        total_count = (await db.execute(total_query)).scalar_one()
        paginated_reports = (
            await db.execute(
                report_query.offset((page - 1) * page_size).limit(page_size)
            )
        ).all()
        report_list = []
        for row in paginated_reports:
            (
                comment_id,
                report_count,
                reporters_data,
                latest_time,
                first_time,
            ) = row
            if reporters_data:
                try:
                    reporters_data_parsed = json.loads(reporters_data)
                except Exception:
                    reporters_data_parsed = []
            else:
                reporters_data_parsed = []
            snapshot_result = await db.execute(
                select(CommentReport.snapshot)
                .where(CommentReport.comment_id == comment_id)
                .order_by(CommentReport.created_at.desc())
                .limit(1)
            )
            snapshot = snapshot_result.scalar_one_or_none()
            comment_info = await db.execute(
                select(Comment, UserProfile, Tweet)
                .join(UserProfile, Comment.user_id == UserProfile.user_id)
                .join(Tweet, Comment.tweet_id == Tweet.id)
                .where(Comment.id == comment_id)
            )
            comment_row = comment_info.first()
            comment_author_name = "Unknown User"
            comment_text = "Comment not found"
            tweet_id = None
            tweet_text = "Tweet not found"
            if comment_row:
                comment, comment_author_profile, tweet = comment_row
                comment_author_name = comment_author_profile.name
                comment_text = (
                    comment.text[:100] + "..."
                    if len(comment.text) > 100
                    else comment.text
                )
                tweet_id = tweet.id
                tweet_text = (
                    tweet.text[:50] + "..." if len(tweet.text) > 50 else tweet.text
                )
            report_list.append(
                {
                    "comment_id": comment_id,
                    "comment_text": comment_text,
                    "comment_author_name": comment_author_name,
                    "tweet_id": tweet_id,
                    "tweet_text": tweet_text,
                    "report_count": report_count,
                    "reporters": reporters_data_parsed,
                    "reporter_count": (
                        len(reporters_data_parsed) if reporters_data_parsed else 0
                    ),
                    "first_reported_at": first_time,
                    "latest_reported_at": latest_time,
                    "latest_snapshot": snapshot,
                    "reasons_summary": (
                        list(set([r["reason"] for r in reporters_data_parsed]))
                        if reporters_data_parsed
                        else []
                    ),
                }
            )
        return ReportListResponse(
            reports=report_list, total=total_count, page=page, page_size=page_size
        )

    async def update_user_status(
        self, db: AsyncSession, request: UpdateUserStatusRequest
    ) -> dict:
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == request.user_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise NotFoundError("User profile not found")
        changed = False
        if request.is_prime is not None:
            profile.is_prime = request.is_prime
            changed = True
        if request.is_organizational is not None:
            profile.is_organizational = request.is_organizational
            changed = True
        if request.is_organizational:
            user_result = await db.execute(
                select(User).where(User.user_id == request.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                user.is_private = False
        if changed:
            await db.commit()
            await cache_service.invalidate_user_cache(request.user_id)
            await cache_service.invalidate_admin_cache()
            return {
                "success": True,
                "message": f"User {request.user_id} status updated",
            }
        else:
            return {"success": False, "message": "No changes provided"}

    async def get_all_users_paginated(
        self, db: AsyncSession, page: int = 1, page_size: int = 20
    ) -> UserSearchResponse:
        cache_key = f"admin:all_users:page:{page}:size:{page_size}"
        cached = await cache_service.get(cache_key)
        if cached:
            return UserSearchResponse(**cached)
        query = (
            select(User, UserProfile)
            .join(UserProfile, User.user_id == UserProfile.user_id)
            .where(User.is_admin == False)
        )
        total = (await db.execute(query)).all()
        total_count = len(total)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = (await db.execute(query)).all()
        users = []
        for user, profile in result:
            users.append(
                {
                    "user_id": user.user_id,
                    "name": profile.name,
                    "is_organizational": profile.is_organizational,
                    "is_private": user.is_private,
                    "is_prime": profile.is_prime,
                    "command_id": profile.command_id,
                    "is_blocked": user.is_blocked,
                }
            )
        response = UserSearchResponse(
            users=users, total=total_count, page=page, page_size=page_size
        )
        await cache_service.set(cache_key, response.model_dump(), ttl=60)
        return response

    async def get_all_blocked_users_paginated(
        self, db: AsyncSession, page: int = 1, page_size: int = 20
    ) -> UserSearchResponse:
        cache_key = f"admin:blocked_users:page:{page}:size:{page_size}"
        cached = await cache_service.get(cache_key)
        if cached:
            return UserSearchResponse(**cached)
        query = (
            select(User, UserProfile)
            .join(UserProfile, User.user_id == UserProfile.user_id)
            .where(User.is_blocked == True)
        )
        total = (await db.execute(query)).all()
        total_count = len(total)
        paginated_query = query.offset((page - 1) * page_size).limit(page_size)
        result = (await db.execute(paginated_query)).all()
        blocked_users_list = []
        for user, profile in result:
            blocked_users_list.append(
                {
                    "user_id": user.user_id,
                    "name": profile.name,
                    "is_organizational": profile.is_organizational,
                    "is_private": user.is_private,
                    "is_prime": profile.is_prime,
                    "command_id": profile.command_id,
                    "is_blocked": user.is_blocked,
                    "block_until": user.block_until,
                }
            )
        response = UserSearchResponse(
            users=blocked_users_list, total=total_count, page=page, page_size=page_size
        )
        await cache_service.set(cache_key, response.model_dump(), ttl=60)
        return response

    async def get_users_by_role(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
        is_prime: Optional[bool] = None,
        is_organizational: Optional[bool] = None,
        is_private: Optional[bool] = None,
    ) -> UserSearchResponse:
        """Get users filtered by role (prime, organizational, or public)"""
        query = (
            select(UserProfile, User)
            .join(User, UserProfile.user_id == User.user_id)
            .where(User.is_admin == False)
        )
        if is_prime is not None:
            query = query.where(UserProfile.is_prime == is_prime)
        if is_organizational is not None:
            query = query.where(UserProfile.is_organizational == is_organizational)
        if is_private is not None:
            query = query.where(User.is_private == is_private)
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        users = result.all()
        user_list = []
        for profile, user in users:
            user_list.append(
                {
                    "user_id": profile.user_id,
                    "name": profile.name,
                    "is_organizational": profile.is_organizational,
                    "is_private": user.is_private,
                    "is_prime": profile.is_prime,
                    "command_id": profile.command_id,
                    "is_blocked": user.is_blocked,
                }
            )
        return UserSearchResponse(
            users=user_list, total=total, page=page, page_size=page_size
        )

    async def get_tweet_stats(
        self, db: AsyncSession, date: datetime
    ) -> TweetStatsResponse:
        """Get tweet statistics for a specific date."""
        start_date = datetime(date.year, date.month, date.day, 0, 0, 0)
        end_date = datetime(date.year, date.month, date.day, 23, 59, 59)
        total_tweets = (
            await db.execute(
                select(func.count(Tweet.id)).where(
                    and_(Tweet.created_at >= start_date, Tweet.created_at <= end_date)
                )
            )
        ).scalar_one()
        total_likes = (
            await db.execute(
                select(func.count())
                .select_from(TweetLike)
                .join(Tweet, TweetLike.tweet_id == Tweet.id)
                .where(
                    and_(Tweet.created_at >= start_date, Tweet.created_at <= end_date)
                )
            )
        ).scalar_one()
        total_comments = (
            await db.execute(
                select(func.count(Comment.id))
                .join(Tweet, Comment.tweet_id == Tweet.id)
                .where(
                    and_(Tweet.created_at >= start_date, Tweet.created_at <= end_date)
                )
            )
        ).scalar_one()
        total_shares = (
            await db.execute(
                select(func.count())
                .select_from(Share)
                .join(Tweet, Share.tweet_id == Tweet.id)
                .where(
                    and_(Tweet.created_at >= start_date, Tweet.created_at <= end_date)
                )
            )
        ).scalar_one()
        total_bookmarks = (
            await db.execute(
                select(func.count())
                .select_from(Bookmark)
                .join(Tweet, Bookmark.tweet_id == Tweet.id)
                .where(
                    and_(Tweet.created_at >= start_date, Tweet.created_at <= end_date)
                )
            )
        ).scalar_one()
        total_views = (
            await db.execute(
                select(func.sum(Tweet.view_count)).where(
                    and_(Tweet.created_at >= start_date, Tweet.created_at <= end_date)
                )
            )
        ).scalar_one() or 0
        return TweetStatsResponse(
            date=date,
            total_tweets=total_tweets,
            total_likes=total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            total_bookmarks=total_bookmarks,
            total_views=total_views,
        )

    async def get_user_details(
        self, db: AsyncSession, user_id: str
    ) -> UserDetailsResponse:
        """Get detailed information about a specific user."""
        try:
            result = await db.execute(
                select(User, UserProfile)
                .join(UserProfile, User.user_id == UserProfile.user_id)
                .where(User.user_id == user_id)
            )
            user_data = result.first()
            if not user_data:
                raise NotFoundError(f"User {user_id} not found")
            user, profile = user_data
            if user.is_admin:
                raise NotFoundError(f"User {user_id} is an admin user")
            tweet_count = (
                await db.scalar(
                    select(func.count(Tweet.id)).where(Tweet.user_id == user_id)
                )
                or 0
            )
            comment_count = (
                await db.scalar(
                    select(func.count(Comment.id)).where(Comment.user_id == user_id)
                )
                or 0
            )
            follower_count = (
                await db.scalar(
                    select(func.count(Follower.followee_id)).where(
                        Follower.followee_id == user_id
                    )
                )
                or 0
            )
            following_count = (
                await db.scalar(
                    select(func.count(Follower.follower_id)).where(
                        Follower.follower_id == user_id
                    )
                )
                or 0
            )
            interests_result = await db.execute(
                select(Interest.name)
                .join(UserInterest, Interest.id == UserInterest.interest_id)
                .where(UserInterest.user_id == user_id)
            )
            interests = [row[0] for row in interests_result.all()]
            command_result = await db.execute(
                select(Command.name).where(Command.id == profile.command_id)
            )
            command_name = command_result.scalar_one_or_none()
            photo = None
            if profile.photo_path and profile.photo_content_type:
                photo = profile.photo_path
            banner = None
            if profile.banner_path and profile.banner_content_type:
                banner = profile.banner_path
            return UserDetailsResponse(
                user_id=user.user_id,
                name=profile.name,
                date_of_birth=user.date_of_birth,
                is_organizational=profile.is_organizational,
                is_private=user.is_private,
                is_prime=profile.is_prime,
                is_active=user.is_active,
                is_online=user.is_online,
                is_blocked=user.is_blocked,
                block_until=user.block_until,
                command_id=profile.command_id,
                command_name=command_name,
                photo=photo,
                banner=banner,
                bio=profile.bio,
                created_at=user.created_at.date() if user.created_at else None,
                tweet_count=tweet_count,
                comment_count=comment_count,
                follower_count=follower_count,
                following_count=following_count,
                interests=interests,
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error while getting user details: {str(e)}")
            raise InternalServerError("Failed to get user details")
        except BaseCustomException as e:
            raise e


admin_service = AdminCruds()
