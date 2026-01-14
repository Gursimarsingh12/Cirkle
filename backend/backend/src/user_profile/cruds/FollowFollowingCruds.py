import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_, desc
from user_profile.models.Follower import Follower
from user_profile.models.FollowRequest import FollowRequest, FollowRequestStatus
from auth.models.User import User
from auth.models.UserProfile import UserProfile
from user_profile.response.FollowRequestResponse import FollowRequestResponse
from caching.cache_service import cache_service
from core.cache_config import CacheConstants, CacheKeyPatterns, get_ttl_for_operation
from datetime import datetime
from core.config import get_settings
from core.exceptions import (
    NotFoundError,
    ValidationError,
    ConflictError,
    BaseCustomException,
)
from core.image_utils import ImageUtils
import asyncio

settings = get_settings()
logger = logging.getLogger(__name__)


class FollowFollowingCruds:
    async def _batch_invalidate_follow_caches(self, follower_id: str, followee_id: str):
        """Optimized batch cache invalidation for follow operations"""
        try:
            # Use batch invalidation instead of individual calls
            await cache_service.batch_invalidate_user_feeds([follower_id, followee_id])
            
            # Invalidate specific follow-related caches
            await cache_service.invalidate_follow_cache(follower_id, followee_id)
            
            # Only invalidate profiles if needed (less aggressive)
            if follower_id != followee_id:  # Sanity check
                profile_tasks = [
                    cache_service.invalidate_profile_cache(follower_id),
                    cache_service.invalidate_profile_cache(followee_id)
                ]
                await asyncio.gather(*profile_tasks, return_exceptions=True)
            
            # Global invalidation only for high-impact accounts
            # Check if followee is a popular account before invalidating recommendations
            # This reduces unnecessary global cache clearing
            
            logger.info(f"Batch invalidated follow caches for {follower_id} -> {followee_id}")
            
        except Exception as e:
            logger.error(f"Failed to batch invalidate follow caches: {e}")
            # Don't raise - cache failures shouldn't break follow operations
            
    async def _smart_cache_warm_up(self, user_ids: list[str], db: AsyncSession):
        """Smart cache warming that only warms critical data"""
        try:
            # Only warm up essential caches, not everything
            for user_id in user_ids:
                # Fire and forget for non-critical warming
                asyncio.create_task(
                    cache_service.smart_cache_warm_up(user_id, db)
                )
        except Exception as e:
            logger.warning(f"Cache warm-up failed, continuing: {e}")

    async def follow_user(
        self, db: AsyncSession, follower_id: str, followee_id: str
    ) -> str:
        if follower_id == followee_id:
            raise ValidationError("Cannot follow yourself")
        follower = (
            await db.execute(select(User).where(User.user_id == follower_id))
        ).scalar_one_or_none()
        followee = (
            await db.execute(select(User).where(User.user_id == followee_id))
        ).scalar_one_or_none()
        if not follower or not followee:
            raise NotFoundError("User not found")
        followee_profile = (
            await db.execute(
                select(UserProfile).where(UserProfile.user_id == followee_id)
            )
        ).scalar_one_or_none()
        if not followee_profile:
            raise NotFoundError("Followee profile not found")
        existing_follow = (
            await db.execute(
                select(Follower).where(
                    and_(
                        Follower.follower_id == follower_id,
                        Follower.followee_id == followee_id,
                    )
                )
            )
        ).scalar_one_or_none()
        if existing_follow:
            raise ConflictError("Already following this user")
        existing_request = (
            await db.execute(
                select(FollowRequest).where(
                    and_(
                        FollowRequest.follower_id == follower_id,
                        FollowRequest.followee_id == followee_id,
                    )
                )
            )
        ).scalar_one_or_none()
        if existing_request:
            if existing_request.status == FollowRequestStatus.pending:
                raise ConflictError("Follow request already pending")
            else:
                existing_request.status = FollowRequestStatus.pending
                existing_request.created_at = datetime.now()
                await db.commit()
                
                # Optimized cache invalidation
                await self._batch_invalidate_follow_caches(follower_id, followee_id)
                await self._smart_cache_warm_up([follower_id, followee_id], db)
                
                return "requested"
        if followee.is_private and not followee_profile.is_organizational:
            follow_request = FollowRequest(
                follower_id=follower_id,
                followee_id=followee_id,
                status=FollowRequestStatus.pending,
            )
            db.add(follow_request)
            await db.commit()
            
            # Optimized cache invalidation  
            await self._batch_invalidate_follow_caches(follower_id, followee_id)
            await self._smart_cache_warm_up([follower_id, followee_id], db)
            
            return "requested"
        else:
            follower_entry = Follower(follower_id=follower_id, followee_id=followee_id)
            db.add(follower_entry)
            await db.commit()
            
            # Optimized cache invalidation
            await self._batch_invalidate_follow_caches(follower_id, followee_id)
            await self._smart_cache_warm_up([follower_id, followee_id], db)
            
            return "followed"

    async def respond_to_follow_request(
        self, db: AsyncSession, follower_id: str, followee_id: str, accept: bool
    ) -> None:
        followee = (
            await db.execute(select(User).where(User.user_id == followee_id))
        ).scalar_one_or_none()
        if not followee:
            raise NotFoundError("User not found")
        follow_request = (
            await db.execute(
                select(FollowRequest).where(
                    and_(
                        FollowRequest.follower_id == follower_id,
                        FollowRequest.followee_id == followee_id,
                        FollowRequest.status == FollowRequestStatus.pending,
                    )
                )
            )
        ).scalar_one_or_none()
        if not follow_request:
            raise NotFoundError("Follow request not found or already processed")
        if accept:
            follow_request.status = FollowRequestStatus.accepted
            follower_entry = Follower(follower_id=follower_id, followee_id=followee_id)
            db.add(follower_entry)
        else:
            follow_request.status = FollowRequestStatus.declined
        await db.commit()
        try:
            await cache_service.invalidate_follow_cache(follower_id, followee_id)
            await cache_service.invalidate_profile_cache(follower_id)
            await cache_service.invalidate_profile_cache(followee_id)
            await cache_service.invalidate_tweet_feed_cache(follower_id)
            await cache_service.invalidate_tweet_feed_cache(followee_id)
            await cache_service.invalidate_twitter_recommendation_cache()
            logger.info(
                f"Invalidated follow-related and profile caches for {follower_id} and {followee_id}"
            )
            asyncio.create_task(cache_service.smart_cache_warm_up(follower_id, db))
            asyncio.create_task(cache_service.smart_cache_warm_up(followee_id, db))
        except BaseCustomException as e:
            logger.error(
                f"Failed to invalidate caches for follow request response: {e}"
            )
            raise

    async def unfollow_user(
        self, db: AsyncSession, follower_id: str, followee_id: str
    ) -> None:
        follower_entry = (
            await db.execute(
                select(Follower).where(
                    and_(
                        Follower.follower_id == follower_id,
                        Follower.followee_id == followee_id,
                    )
                )
            )
        ).scalar_one_or_none()
        if not follower_entry:
            raise ValidationError("Not following this user")
        await db.delete(follower_entry)
        await db.commit()
        try:
            await cache_service.invalidate_follow_cache(follower_id, followee_id)
            await cache_service.invalidate_profile_cache(follower_id)
            await cache_service.invalidate_profile_cache(followee_id)
            await cache_service.invalidate_tweet_feed_cache(follower_id)
            await cache_service.invalidate_tweet_feed_cache(followee_id)
            await cache_service.invalidate_twitter_recommendation_cache()
            logger.info(
                f"Invalidated follow-related and profile caches for {follower_id} and {followee_id}"
            )
            asyncio.create_task(cache_service.smart_cache_warm_up(follower_id, db))
            asyncio.create_task(cache_service.smart_cache_warm_up(followee_id, db))
        except BaseCustomException as e:
            logger.error(f"Failed to invalidate caches for unfollow action: {e}")
            raise

    async def remove_follower(
        self, db: AsyncSession, user_id: str, follower_id: str
    ) -> None:
        """Remove a follower from the user's follower list"""
        if user_id == follower_id:
            raise ValidationError("Cannot remove yourself as a follower")
        
        # Check if the user exists
        user = (
            await db.execute(select(User).where(User.user_id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        
        # Check if the follower exists
        follower = (
            await db.execute(select(User).where(User.user_id == follower_id))
        ).scalar_one_or_none()
        if not follower:
            raise NotFoundError("Follower not found")
        
        # Check if the follower relationship exists
        follower_entry = (
            await db.execute(
                select(Follower).where(
                    and_(
                        Follower.follower_id == follower_id,
                        Follower.followee_id == user_id,
                    )
                )
            )
        ).scalar_one_or_none()
        
        if not follower_entry:
            raise ValidationError("This user is not following you")
        
        # Remove the follower relationship
        await db.delete(follower_entry)
        
        # Also remove any pending follow request from the same user
        pending_request = (
            await db.execute(
                select(FollowRequest).where(
                    and_(
                        FollowRequest.follower_id == follower_id,
                        FollowRequest.followee_id == user_id,
                        FollowRequest.status == FollowRequestStatus.pending,
                    )
                )
            )
        ).scalar_one_or_none()
        
        if pending_request:
            await db.delete(pending_request)
        
        await db.commit()
        
        # Comprehensive cache invalidation
        try:
            await cache_service.invalidate_follower_removal_cache(user_id, follower_id)
            logger.info(
                f"Successfully removed follower {follower_id} from {user_id} and invalidated all related caches"
            )
            asyncio.create_task(cache_service.smart_cache_warm_up(user_id, db))
            asyncio.create_task(cache_service.smart_cache_warm_up(follower_id, db))
        except BaseCustomException as e:
            logger.error(f"Failed to invalidate caches for remove follower action: {e}")
            raise

    async def get_follow_requests(
        self, db: AsyncSession, user_id: str
    ) -> list[FollowRequestResponse]:
        cache_key = f"follow_requests:{user_id}"
        cached_requests = await cache_service.get(cache_key)
        if cached_requests:
            return [FollowRequestResponse(**req) for req in cached_requests]
        user = (
            await db.execute(select(User).where(User.user_id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        requests = (
            (
                await db.execute(
                    select(FollowRequest).where(
                        (FollowRequest.followee_id == user_id)
                        & (FollowRequest.status == FollowRequestStatus.pending)
                    )
                )
            )
            .scalars()
            .all()
        )
        result = []
        for req in requests:
            requester_profile = (
                await db.execute(
                    select(UserProfile).where(UserProfile.user_id == req.follower_id)
                )
            ).scalar_one_or_none()
            if requester_profile:
                resp = FollowRequestResponse(
                    follower_id=req.follower_id,
                    name=requester_profile.name,
                    photo=(
                        requester_profile.photo_path
                        if requester_profile.photo_path
                        and requester_profile.photo_content_type
                        else None
                    ),
                    created_at=req.created_at.isoformat() if req.created_at else None,
                    is_private=(
                        (
                            await db.execute(
                                select(User).where(User.user_id == req.follower_id)
                            )
                        )
                        .scalar_one_or_none()
                        .is_private
                        if req.follower_id
                        else False
                    ),
                    is_prime=requester_profile.is_prime,
                    is_organizational=requester_profile.is_organizational,
                )
                result.append(resp.model_dump())
        try:
            cache_data = result
            if cache_data:
                for req in cache_data:
                    req["created_at"] = (
                        req["created_at"].isoformat() if req["created_at"] else None
                    )
            await cache_service.set(
                cache_key, cache_data, ttl=settings.FOLLOW_REQUESTS_CACHE_TTL
            )
            logger.info(f"Cached follow requests for {user_id}")
        except BaseCustomException as e:
            logger.error(f"Failed to cache follow requests for {user_id}: {e}")
            raise
        return [FollowRequestResponse(**r) for r in result]

    async def get_followers(
        self, db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[FollowRequestResponse], int]:
        offset = (page - 1) * page_size
        cache_key = f"followers:{user_id}:p{page}:s{page_size}"
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for followers: {cache_key}")
            return [FollowRequestResponse(**f) for f in cached_data["followers"]], cached_data["total"]
        logger.info(f"Cache miss for followers: {cache_key}")
        user = (
            await db.execute(select(User).where(User.user_id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        try:
            total_query = select(func.count()).where(Follower.followee_id == user_id)
            total = (await db.execute(total_query)).scalar_one()
            
            followers_query = (
                select(Follower, UserProfile)
                .join(UserProfile, Follower.follower_id == UserProfile.user_id)
                .where(Follower.followee_id == user_id)
                .order_by(desc(Follower.created_at))
                .offset(offset)
                .limit(page_size)
            )
            followers_result = await db.execute(followers_query)
            follower_rows = followers_result.all()
            follower_objs = []
            for follower, profile in follower_rows:
                resp = FollowRequestResponse(
                    follower_id=follower.follower_id,
                    name=profile.name if profile else "Unknown User",
                    photo=(
                        profile.photo_path
                        if profile and profile.photo_path and profile.photo_content_type
                        else None
                    ),
                    created_at=(
                        follower.created_at.isoformat() if follower.created_at else None
                    ),
                    is_private=(
                        (
                            await db.execute(
                                select(User).where(User.user_id == follower.follower_id)
                            )
                        )
                        .scalar_one_or_none()
                        .is_private
                        if follower.follower_id
                        else False
                    ),
                    is_prime=profile.is_prime if profile else False,
                    is_organizational=profile.is_organizational if profile else False,
                )
                follower_objs.append(resp.model_dump())
            cache_ttl = 1800 if len(follower_objs) < page_size else 900
            cache_data = {"followers": follower_objs, "total": total}
            await cache_service.set(cache_key, cache_data, ttl=cache_ttl)
            logger.info(f"Cached followers for {user_id}")
            asyncio.create_task(cache_service.smart_cache_warm_up(user_id, db))
            return [FollowRequestResponse(**f) for f in follower_objs], total
        except BaseCustomException as e:
            logger.error(f"Error getting followers for {user_id}: {str(e)}")
            raise

    async def get_following(
        self, db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[FollowRequestResponse], int]:
        offset = (page - 1) * page_size
        cache_key = f"following:{user_id}:p{page}:s{page_size}"
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for following: {cache_key}")
            return [FollowRequestResponse(**f) for f in cached_data["following"]], cached_data["total"]
        logger.info(f"Cache miss for following: {cache_key}")
        user = (
            await db.execute(select(User).where(User.user_id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        try:
            total_query = select(func.count()).where(Follower.follower_id == user_id)
            total = (await db.execute(total_query)).scalar_one()
            
            following_query = (
                select(Follower, UserProfile)
                .join(UserProfile, Follower.followee_id == UserProfile.user_id)
                .where(Follower.follower_id == user_id)
                .order_by(desc(Follower.created_at))
                .offset(offset)
                .limit(page_size)
            )
            following_result = await db.execute(following_query)
            following_rows = following_result.all()
            following_objs = []
            for follow, profile in following_rows:
                resp = FollowRequestResponse(
                    follower_id=follow.followee_id,
                    name=profile.name if profile else "Unknown User",
                    photo=(
                        profile.photo_path
                        if profile and profile.photo_path and profile.photo_content_type
                        else None
                    ),
                    created_at=(
                        follow.created_at.isoformat() if follow.created_at else None
                    ),
                    is_private=(
                        (
                            await db.execute(
                                select(User).where(User.user_id == follow.followee_id)
                            )
                        )
                        .scalar_one_or_none()
                        .is_private
                        if follow.followee_id
                        else False
                    ),
                    is_prime=profile.is_prime if profile else False,
                    is_organizational=profile.is_organizational if profile else False,
                )
                following_objs.append(resp.model_dump())
            cache_ttl = 1800 if len(following_objs) < page_size else 900
            cache_data = {"following": following_objs, "total": total}
            await cache_service.set(cache_key, cache_data, ttl=cache_ttl)
            logger.info(f"Cached following for {user_id}")
            asyncio.create_task(cache_service.smart_cache_warm_up(user_id, db))
            return [FollowRequestResponse(**f) for f in following_objs], total
        except BaseCustomException as e:
            logger.error(f"Error getting following for {user_id}: {str(e)}")
            raise

    async def get_new_followers(
        self,
        db: AsyncSession,
        user_id: str,
        since: datetime = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[FollowRequestResponse], int]:
        user = (
            await db.execute(select(User).where(User.user_id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        query = select(Follower).where(Follower.followee_id == user_id)
        if since:
            query = query.where(Follower.created_at >= since)
        
        total_query = query
        total = (await db.execute(select(func.count()).select_from(total_query.subquery()))).scalar_one()
        
        offset = (page - 1) * page_size
        new_followers = (
            (await db.execute(query.order_by(desc(Follower.created_at)).offset(offset).limit(page_size)))
            .scalars()
            .all()
        )
        result = []
        for follower in new_followers:
            profile = (
                await db.execute(
                    select(UserProfile).where(
                        UserProfile.user_id == follower.follower_id
                    )
                )
            ).scalar_one_or_none()
            resp = FollowRequestResponse(
                follower_id=follower.follower_id,
                name=profile.name if profile else None,
                photo=(
                    profile.photo_path
                    if profile and profile.photo_path and profile.photo_content_type
                    else None
                ),
                created_at=(
                    follower.created_at.isoformat() if follower.created_at else None
                ),
                is_private=(
                    (
                        await db.execute(
                            select(User).where(User.user_id == follower.follower_id)
                        )
                    )
                    .scalar_one_or_none()
                    .is_private
                    if follower.follower_id
                    else False
                ),
                is_prime=profile.is_prime if profile else False,
                is_organizational=profile.is_organizational if profile else False,
            )
            result.append(resp.model_dump())
        return [FollowRequestResponse(**r) for r in result], total

    async def get_mutual_followers(
        self, db: AsyncSession, user_id: str
    ) -> list[FollowRequestResponse]:
        followers_list, _ = await self.get_followers(db, user_id)
        following_list, _ = await self.get_following(db, user_id)
        followers_dict = {f.follower_id: f for f in followers_list}
        following_dict = {f.follower_id: f for f in following_list}
        mutual_ids = set(followers_dict.keys()) & set(following_dict.keys())
        mutuals = [followers_dict[uid] for uid in mutual_ids]
        return mutuals


follow_service = FollowFollowingCruds()
