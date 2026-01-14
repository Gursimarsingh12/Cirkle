from datetime import datetime
import re
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, or_, desc
from sqlalchemy.orm import selectinload, aliased
from user_profile.cruds.InterestCruds import interest_service
from user_profile.models.Follower import Follower
from auth.models.User import User
from auth.models.UserProfile import UserProfile
from user_profile.models.Interest import Interest
from user_profile.models.UserInterest import UserInterest
from user_profile.response.ProfileResponse import ProfileResponse
from user_profile.request.UpdateProfileRequest import UpdateProfileRequest
from caching.cache_service import cache_service
from core.cache_config import CacheConstants, CacheKeyPatterns, get_ttl_for_operation, should_use_lock, get_lock_ttl
from core.exceptions import (
    BaseCustomException,
    NotFoundError,
    ValidationError,
)
from core.config import get_settings
from user_profile.request.UserSearchRequest import UserSearchRequest
from user_profile.response.UserSearchResponse import UserSearchResponse
from user_profile.response.TopAccountsResponse import TopAccountsResponse, TopAccount
from core.image_utils import ImageUtils
from user_profile.models.FollowRequest import FollowRequest, FollowRequestStatus

settings = get_settings()
logger = logging.getLogger(__name__)


class UserProfileCruds:
    async def get_user_profile(
        self, db: AsyncSession, user_id: str, requester_id: str = None
    ) -> ProfileResponse:
        # Use standardized cache key pattern
        cache_key = CacheKeyPatterns.PROFILE.format(
            user_id=user_id, 
            requester_id=requester_id or 'none'
        )
        
        # Use cache stampede protection for expensive profile queries
        if should_use_lock('profile', estimated_compute_time=2.0):
            try:
                async def compute_profile():
                    return await self._compute_profile_internal(db, user_id, requester_id)
                
                cached_result = await cache_service.cache_with_lock(
                    cache_key,
                    compute_profile,
                    ttl=get_ttl_for_operation('profile'),
                    lock_ttl=get_lock_ttl('profile', 2.0)
                )
                
                if cached_result:
                    return ProfileResponse(**cached_result)
                    
            except Exception as e:
                logger.warning(f"Cache with lock failed for profile {user_id}: {e}")
                # Fallback to direct computation
        
        # Direct computation if lock not used or failed
        return await self._compute_profile_internal(db, user_id, requester_id)
    
    async def _compute_profile_internal(
        self, db: AsyncSession, user_id: str, requester_id: str = None
    ) -> ProfileResponse:
        """Internal method for computing user profile - original logic moved here"""
        cache_key = CacheKeyPatterns.PROFILE.format(
            user_id=user_id, 
            requester_id=requester_id or 'none'
        )
        
        try:
            cached_profile = await cache_service.get(cache_key)
            if cached_profile:
                logger.info(
                    f"Cache hit for profile {user_id} (requester: {requester_id})"
                )
                return ProfileResponse(**cached_profile)
        except Exception as e:
            logger.warning(f"Cache retrieval failed for {cache_key}: {e}")
            # Continue without cache instead of failing
            
        logger.info(f"Cache miss for profile {user_id} (requester: {requester_id})")
        try:
            user_profile_query = (
                select(User, UserProfile)
                .join(UserProfile, User.user_id == UserProfile.user_id)
                .options(selectinload(User.command))
                .where(User.user_id == user_id)
            )
            result = await db.execute(user_profile_query)
            user_profile_row = result.first()
            if not user_profile_row:
                raise NotFoundError("User not found")
            user, profile = user_profile_row
            if user.block_until and user.block_until <= datetime.now().date():
                user.is_blocked = False
                user.block_until = None
                await db.commit()
                # Invalidate cache after unblocking
                try:
                    await cache_service.invalidate_profile_cache(user_id)
                except Exception as e:
                    logger.warning(f"Failed to invalidate cache after unblocking: {e}")
                    
            if user.is_blocked:
                raise ValidationError(
                    "This account has been blocked permanently. Please contact support."
                )
            if user.block_until and user.block_until > datetime.now().date():
                raise ValidationError(
                    f"This account has been blocked until {user.block_until}. Please contact support."
                )
            batch_queries = [
                select(Interest.name)
                .join(UserInterest)
                .where(UserInterest.user_id == user_id),
                select(func.count())
                .select_from(Follower)
                .where(Follower.followee_id == user_id),
                select(func.count())
                .select_from(Follower)
                .where(Follower.follower_id == user_id),
            ]
            interests_result = await db.execute(batch_queries[0])
            interests = [name for name in interests_result.scalars().all()]
            followers_count = (await db.execute(batch_queries[1])).scalar_one() or 0
            following_count = (await db.execute(batch_queries[2])).scalar_one() or 0
            if profile.photo_path and profile.photo_content_type:
                photo = profile.photo_path
            else:
                photo = None
            if profile.banner_path and profile.banner_content_type:
                banner = profile.banner_path
            else:
                banner = None
            if requester_id is None or requester_id == user_id:
                follow_status = "self"
            else:
                follow_status = "not_following"
                follow_check = await db.execute(
                    select(Follower).where(
                        Follower.follower_id == requester_id,
                        Follower.followee_id == user_id,
                    )
                )
                is_follower = follow_check.scalar_one_or_none() is not None
                if is_follower:
                    follow_status = "following"
                else:
                    request_check = await db.execute(
                        select(FollowRequest).where(
                            FollowRequest.follower_id == requester_id,
                            FollowRequest.followee_id == user_id,
                            FollowRequest.status == FollowRequestStatus.pending,
                        )
                    )
                    is_requested = request_check.scalar_one_or_none() is not None
                    if is_requested:
                        follow_status = "requested"
            response = ProfileResponse(
                user_id=user.user_id,
                name=profile.name,
                bio=profile.bio,
                photo=photo,
                banner=banner,
                is_private=user.is_private,
                is_organizational=profile.is_organizational,
                is_prime=profile.is_prime,
                is_online=user.is_online,
                followers_count=followers_count,
                following_count=following_count,
                interests=interests,
                command=user.command.name if user.command else "",
                mutual_followers=[],
                can_view_content=True,
                created_at=user.created_at,
                updated_at=profile.updated_at,
                message="",
                follow_status=follow_status,
            )
            if user.is_blocked:
                response.message = (
                    "This account is permanently blocked. Please contact support."
                )
            elif user.block_until and user.block_until > datetime.now().date():
                response.message = f"This account is blocked until {user.block_until}."
            if not user.is_private:
                response.can_view_content = True
                
            # Use standardized TTL
            cache_ttl = get_ttl_for_operation('profile', is_empty=False)
            
            try:
                await cache_service.set(cache_key, response.model_dump(), ttl=cache_ttl)
                logger.info(f"Profile cached for {user_id} with key {cache_key}")
            except Exception as e:
                logger.warning(f"Failed to cache profile for {user_id}: {e}")
                # Continue without caching instead of failing
                
            return response
        except BaseCustomException as e:
            raise e

    async def update_user_profile(
        self, db: AsyncSession, user_id: str, request: UpdateProfileRequest
    ) -> ProfileResponse:
        try:
            user = await db.execute(select(User).filter(User.user_id == user_id))
            user = user.scalar_one_or_none()
            if not user:
                raise NotFoundError("User not found")
            if user.block_until and user.block_until <= datetime.now().date():
                user.is_blocked = False
                user.block_until = None
                await db.commit()
            if user.is_blocked:
                raise ValidationError(
                    "Your account is permanently blocked. Please contact support."
                )
            if user.block_until and user.block_until > datetime.now().date():
                raise ValidationError(
                    f"Your account is blocked until {user.block_until}. Please try again later."
                )
            profile = await db.execute(
                select(UserProfile).filter(UserProfile.user_id == user_id)
            )
            profile = profile.scalar_one_or_none()
            if not profile:
                raise NotFoundError("Profile not found")
            if request.name is not None:
                profile.name = request.name
            if request.bio is not None:
                profile.bio = request.bio
            if request.is_private is not None:
                user.is_private = request.is_private
            if request.command_id is not None:
                user.command_id = request.command_id
            if request.photo_bytes is not None and request.photo_content_type:
                allowed_types = ImageUtils.ALLOWED_TYPES
                if request.photo_content_type not in allowed_types:
                    raise ValidationError(
                        f"Invalid photo content type: {request.photo_content_type}. Allowed: {allowed_types}"
                    )
                ext = request.photo_content_type.split("/")[-1]
                photo_path = ImageUtils.save_user_photo(
                    user_id, request.photo_bytes, ext
                )
                profile.photo_path = photo_path
                profile.photo_content_type = request.photo_content_type
                logger.info(f"Saved and updated photo for user {user_id}: {photo_path}")
            if request.banner_bytes is not None and request.banner_content_type:
                allowed_types = ImageUtils.ALLOWED_TYPES
                if request.banner_content_type not in allowed_types:
                    raise ValidationError(
                        f"Invalid banner content type: {request.banner_content_type}. Allowed: {allowed_types}"
                    )
                ext = request.banner_content_type.split("/")[-1]
                banner_path = ImageUtils.save_user_banner(
                    user_id, request.banner_bytes, ext
                )
                profile.banner_path = banner_path
                profile.banner_content_type = request.banner_content_type
                logger.info(
                    f"Saved and updated banner for user {user_id}: {banner_path}"
                )
            if request.interest_ids is not None:
                if len(request.interest_ids) > 8:
                    raise ValidationError("You can only add up to 8 interests.")
                await interest_service.set_user_interests(
                    db, user_id, request.interest_ids
                )
            profile.updated_at = datetime.now()
            await db.commit()
            logger.info(f"Updated profile for user {user_id}")
            try:
                # Comprehensive cache invalidation for profile update
                await cache_service.invalidate_profile_cache(user_id)
                await cache_service.invalidate_interests_cache(user_id)
                await cache_service.invalidate_user_cache(user_id)  # Invalidate broader user cache
                if request.is_private is not None:
                    # If privacy setting changed, invalidate feeds
                    await cache_service.invalidate_tweet_feed_cache(user_id)
                    await cache_service.invalidate_twitter_recommendation_cache()
            except BaseCustomException as e:
                logger.warning(f"Failed to invalidate cache for user {user_id}: {e}")
                raise e
            return await self.get_user_profile(db, user_id)
        except BaseCustomException as e:
            raise e

    async def search_users(
        self, db: AsyncSession, request: UserSearchRequest
    ) -> UserSearchResponse:
        cache_key = f"user_search:{request.search or 'all'}:p{request.page}"
        cached = await cache_service.get(cache_key)
        if cached:
            logger.info(f"Cache hit for user search: {cache_key}")
            return UserSearchResponse(**cached)
        logger.info(f"Cache miss for user search: {cache_key}")
        page_size = 20
        offset = (request.page - 1) * page_size
        try:
            filters = [User.is_blocked == False, User.is_admin == False]
            if request.search:
                search_term = f"%{request.search}%"
                if re.match(r"^[A-Z]{2}[0-9]{5}$", request.search):
                    filters.append(User.user_id == request.search)
                else:
                    filters.append(
                        or_(
                            User.user_id.ilike(search_term),
                            UserProfile.name.ilike(search_term),
                        )
                    )
            count_query = (
                select(func.count(User.user_id))
                .select_from(User)
                .join(UserProfile, User.user_id == UserProfile.user_id)
                .where(*filters)
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
                .where(*filters)
                .order_by(UserProfile.name)
                .offset(offset)
                .limit(page_size)
            )
            result = (await db.execute(query)).all()
            users = []
            for user, profile in result:
                photo = None
                if profile.photo_path and profile.photo_content_type:
                    photo = profile.photo_path
                users.append(
                    {"user_id": user.user_id, "name": profile.name, "photo": photo}
                )
            response = UserSearchResponse(
                users=users, total=total_count, page=request.page, page_size=page_size
            )
            cache_ttl = 600 if request.search else 1800
            await cache_service.set(cache_key, response.model_dump(), ttl=cache_ttl)
            return response
        except BaseCustomException as e:
            raise e

    async def get_top_accounts(
        self, db: AsyncSession, limit: int = 10
    ) -> TopAccountsResponse:
        half = limit // 2
        followers_count_subq = (
            select(
                Follower.followee_id.label("user_id"),
                func.count(Follower.follower_id).label("followers_count"),
            )
            .group_by(Follower.followee_id)
            .subquery()
        )
        subq_alias = aliased(followers_count_subq)
        prime_org_result = await db.execute(
            select(
                UserProfile.user_id,
                UserProfile.name,
                UserProfile.photo_path,
                UserProfile.photo_content_type,
                UserProfile.is_organizational,
                UserProfile.is_prime,
                func.coalesce(subq_alias.c.followers_count, 0).label("followers_count"),
            )
            .join(User, User.user_id == UserProfile.user_id)
            .outerjoin(subq_alias, UserProfile.user_id == subq_alias.c.user_id)
            .where(
                UserProfile.is_prime == True,
                UserProfile.is_organizational == True,
                User.is_blocked == False,
                User.is_active == True,
            )
            .order_by(desc("followers_count"))
            .limit(half)
        )
        prime_org_accounts = [
            TopAccount(
                user_id=row.user_id,
                name=row.name,
                photo=(
                    row.photo_path
                    if row.photo_path and row.photo_content_type
                    else None
                ),
                followers_count=row.followers_count,
                is_organizational=row.is_organizational,
                is_prime=row.is_prime,
            )
            for row in prime_org_result
        ]
        prime_followers_result = await db.execute(
            select(
                UserProfile.user_id,
                UserProfile.name,
                UserProfile.photo_path,
                UserProfile.photo_content_type,
                UserProfile.is_organizational,
                UserProfile.is_prime,
                func.coalesce(subq_alias.c.followers_count, 0).label("followers_count"),
            )
            .join(User, User.user_id == UserProfile.user_id)
            .outerjoin(subq_alias, UserProfile.user_id == subq_alias.c.user_id)
            .where(
                UserProfile.is_prime == True,
                UserProfile.is_organizational == False,
                User.is_blocked == False,
                User.is_active == True,
            )
            .order_by(desc("followers_count"))
            .limit(half)
        )
        prime_followers_accounts = [
            TopAccount(
                user_id=row.user_id,
                name=row.name,
                photo=(
                    row.photo_path
                    if row.photo_path and row.photo_content_type
                    else None
                ),
                followers_count=row.followers_count,
                is_organizational=row.is_organizational,
                is_prime=row.is_prime,
            )
            for row in prime_followers_result
        ]
        seen = set()
        result = []
        for acc in prime_org_accounts:
            if acc.user_id not in seen and len(result) < limit:
                result.append(acc)
                seen.add(acc.user_id)
        for acc in prime_followers_accounts:
            if acc.user_id not in seen and len(result) < limit:
                result.append(acc)
                seen.add(acc.user_id)
        if len(result) < limit:
            extra_org_result = await db.execute(
                select(
                    UserProfile.user_id,
                    UserProfile.name,
                    UserProfile.photo_path,
                    UserProfile.photo_content_type,
                    UserProfile.is_organizational,
                    UserProfile.is_prime,
                    func.coalesce(subq_alias.c.followers_count, 0).label(
                        "followers_count"
                    ),
                )
                .join(User, User.user_id == UserProfile.user_id)
                .outerjoin(subq_alias, UserProfile.user_id == subq_alias.c.user_id)
                .where(
                    UserProfile.is_prime == True,
                    UserProfile.is_organizational == True,
                    User.is_blocked == False,
                    User.is_active == True,
                    ~UserProfile.user_id.in_(seen),
                )
                .order_by(desc("followers_count"))
                .limit(limit - len(result))
            )
            for row in extra_org_result:
                if row.user_id not in seen and len(result) < limit:
                    result.append(
                        TopAccount(
                            user_id=row.user_id,
                            name=row.name,
                            photo=(
                                row.photo_path
                                if row.photo_path and row.photo_content_type
                                else None
                            ),
                            followers_count=row.followers_count,
                            is_organizational=row.is_organizational,
                            is_prime=row.is_prime,
                        )
                    )
                    seen.add(row.user_id)
        if len(result) < limit:
            extra_followers_result = await db.execute(
                select(
                    UserProfile.user_id,
                    UserProfile.name,
                    UserProfile.photo_path,
                    UserProfile.photo_content_type,
                    UserProfile.is_organizational,
                    UserProfile.is_prime,
                    func.coalesce(subq_alias.c.followers_count, 0).label(
                        "followers_count"
                    ),
                )
                .join(User, User.user_id == UserProfile.user_id)
                .outerjoin(subq_alias, UserProfile.user_id == subq_alias.c.user_id)
                .where(
                    UserProfile.is_prime == True,
                    UserProfile.is_organizational == False,
                    User.is_blocked == False,
                    User.is_active == True,
                    ~UserProfile.user_id.in_(seen),
                )
                .order_by(desc("followers_count"))
                .limit(limit - len(result))
            )
            for row in extra_followers_result:
                if row.user_id not in seen and len(result) < limit:
                    result.append(
                        TopAccount(
                            user_id=row.user_id,
                            name=row.name,
                            photo=(
                                row.photo_path
                                if row.photo_path and row.photo_content_type
                                else None
                            ),
                            followers_count=row.followers_count,
                            is_organizational=row.is_organizational,
                            is_prime=row.is_prime,
                        )
                    )
                    seen.add(row.user_id)
        return TopAccountsResponse(accounts=result)


user_profile_service = UserProfileCruds()
