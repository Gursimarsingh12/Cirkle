import json
import hashlib
import logging
import asyncio
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_, or_, case
from sqlalchemy.orm import aliased
from tweets.response.SharedTweetResponse import SharedTweetResponse
from tweets.models.TweetMedia import TweetMedia
from tweets.models.Tweet import Tweet
from tweets.models.TweetLike import TweetLike
from tweets.models.Bookmark import Bookmark
from tweets.models.Share import Share
from tweets.models.Comment import Comment
from tweets.models.CommentLike import CommentLike
from tweets.models.CommentReport import CommentReport
from tweets.models.TweetReport import TweetReport
from tweets.request.PostTweetRequest import PostTweetRequest
from tweets.request.LikeTweetRequest import LikeTweetRequest
from tweets.request.BookmarkTweetRequest import BookmarkTweetRequest
from tweets.request.ShareTweetRequest import ShareTweetRequest
from tweets.request.ReportTweetRequest import ReportTweetRequest
from tweets.request.CommentTweetRequest import CommentTweetRequest
from tweets.request.LikeCommentRequest import LikeCommentRequest
from tweets.request.ReportCommentRequest import ReportCommentRequest
from tweets.response.TweetResponse import (
    TweetResponse,
    CommentResponse,
    TweetMediaResponse,
)
from tweets.response.TweetFeedResponse import TweetFeedResponse
from tweets.response.ActionResponse import ActionResponse
from core.config import get_settings
from core.exceptions import (
    BaseCustomException,
    NotFoundError,
    ValidationError,
    InternalServerError,
)
from core.logging import setup_logging
from core.image_utils import ImageUtils
from caching.cache_service import cache_service
from user_profile.models.Follower import Follower
from user_profile.cruds.UserProfileCruds import user_profile_service
from auth.models.User import User
from auth.models.UserProfile import UserProfile
from user_profile.cruds.FollowFollowingCruds import follow_service

setup_logging()
logger = logging.getLogger("tweets")
settings = get_settings()


class TweetCruds:
    def __init__(self):
        self.settings = get_settings()

    def convert_datetime_to_json_serializable(self, obj):
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        elif hasattr(obj, "date") and hasattr(obj.date(), "isoformat"):
            return obj.date().isoformat()
        else:
            return str(obj)

    async def _check_and_auto_unblock_user(self, db: AsyncSession, user_id: str):
        user = (
            await db.execute(select(User).where(User.user_id == user_id))
        ).scalar_one_or_none()
        if user:
            if user.block_until is not None and user.block_until <= datetime.now().date():
                user.is_blocked = False
                user.block_until = None
                await db.commit()
            if user.is_blocked is True:
                raise ValidationError(
                    "Your account is permanently blocked. Please contact support."
                )
            if user.block_until is not None and user.block_until > datetime.now().date():
                raise ValidationError(
                    f"Your account is blocked until {user.block_until}. Please try again later."
                )

    async def post_tweet(
        self, db: AsyncSession, user_id: str, request: dict
    ) -> TweetResponse:
        await self._check_and_auto_unblock_user(db, user_id)
        if not request["text"] or not request["text"].strip():
            raise ValidationError("Tweet text is required")
        if len(request["text"]) > 500:
            raise ValidationError("Tweet text cannot exceed 500 characters")
        if len(request.get("media", []) or []) > settings.MAX_TWEET_IMAGES:
            raise ValidationError("A tweet can have at most 4 media items.")

        allowed_types = ImageUtils.ALLOWED_TYPES
        if request.get("media"):
            for m in request["media"]:
                if m["media_type"] not in allowed_types:
                    raise ValidationError(
                        f"Invalid media_type: {m['media_type']}. Allowed: {allowed_types}"
                    )

        tweet = Tweet(user_id=user_id, text=request["text"])
        db.add(tweet)
        await db.flush()
        await db.refresh(tweet)
        if request.get("media"):
            for idx, m in enumerate(request["media"]):
                if "media_bytes" in m and m["media_bytes"] is not None:
                    ext = m["media_type"].split("/")[-1]
                    file_data = m["media_bytes"]
                    media_path = ImageUtils.save_tweet_media(
                        user_id, tweet.id, idx + 1, file_data, ext
                    )
                else:
                    media_path = m["media_path"]
                tweet_media = TweetMedia(
                    tweet_id=tweet.id,
                    media_type=m["media_type"],
                    media_path=media_path,
                )
                db.add(tweet_media)
        try:
            await db.commit()
            # Comprehensive cache invalidation for new tweet
            await cache_service.invalidate_feed_for_followers(db, user_id)
            await cache_service.invalidate_user_cache(user_id)
            await cache_service.invalidate_twitter_recommendation_cache()
            await cache_service.invalidate_engagement_cache(tweet.id)
            await cache_service.invalidate_user_interaction_cache(user_id, "all")
            return await self.get_tweet_response(db, tweet.id, user_id)
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to post tweet: {e}")
            raise e

    async def edit_tweet(
        self,
        db: AsyncSession,
        user_id: str,
        tweet_id: int,
        text: str = None,
        media: list = None,
    ) -> TweetResponse:
        await self._check_and_auto_unblock_user(db, user_id)
        logger.info(f"media summary: {[{k: m[k] for k in ['media_path', 'existing'] if k in m} for m in media]}")
        tweet = (
            await db.execute(
                select(Tweet).where(Tweet.id == tweet_id, Tweet.user_id == user_id)
            )
        ).scalar_one_or_none()
        if not tweet:
            raise NotFoundError("Tweet not found or not owned by user")
        updated = False
        if text is not None:
            if not text.strip():
                raise ValidationError("Tweet text cannot be empty")
            if len(text) > 500:
                raise ValidationError("Tweet text cannot exceed 500 characters")
            tweet.text = text
            tweet.edited_at = datetime.utcnow()
            updated = True
        if media is not None:
            allowed_types = ImageUtils.ALLOWED_TYPES
            # Separate existing and new media
            existing_paths = set()
            new_media = []
            for m in media:
                if m.get("existing"):
                    existing_paths.add(m["media_path"])
                else:
                    new_media.append(m)
            # Fetch current media for the tweet
            current_media = (
                await db.execute(
                    select(TweetMedia).where(TweetMedia.tweet_id == tweet_id)
                )
            ).scalars().all()
            logger.info(f"current_media paths: {[m.media_path for m in current_media]}")
            logger.info(f"existing_paths: {list(existing_paths)}")
            logger.info(f"new_media paths: {[m['media_path'] for m in new_media]}")
            # Delete media not in existing_paths
            for m in current_media:
                if m.media_path not in existing_paths:
                    await db.delete(m)
            # Add new media
            for idx, m in enumerate(new_media):
                if m["media_type"] not in allowed_types:
                    raise ValidationError(
                        f"Invalid media_type: {m['media_type']}. Allowed: {allowed_types}"
                    )
                ext = m["media_type"].split("/")[-1]
                file_data = m["media_bytes"]
                media_path = m["media_path"]
                tweet_media = TweetMedia(
                    tweet_id=tweet.id,
                    media_type=m["media_type"],
                    media_path=media_path,
                )
                db.add(tweet_media)
            updated = True
        if not updated:
            raise ValidationError("No changes provided for tweet edit.")
        try:
            await db.commit()
            await db.refresh(tweet)
            await cache_service.invalidate_feed_for_followers(db, user_id)
            await cache_service.invalidate_user_cache(user_id)
            await cache_service.invalidate_twitter_recommendation_cache()
            await cache_service.invalidate_engagement_cache(tweet.id)
            return await self.get_tweet_response(db, tweet.id, user_id)
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to edit tweet: {e}")
            raise e

    async def get_tweet_response(
        self, db: AsyncSession, tweet_id: int, user_id: str
    ) -> TweetResponse:
        cache_key = f"tweet_response:{tweet_id}:u{user_id}"
        cached = await cache_service.get(cache_key)
        if cached:
            return TweetResponse(**cached)
        tweet_query = (
            select(Tweet, UserProfile, User)
            .join(UserProfile, Tweet.user_id == UserProfile.user_id)
            .join(User, User.user_id == Tweet.user_id)
            .where(Tweet.id == tweet_id)
        )
        result = await db.execute(tweet_query)
        tweet_data = result.first()
        if not tweet_data:
            raise NotFoundError("Tweet not found")
        tweet, profile, user_obj = tweet_data
        like_count = len(
            (await db.execute(select(TweetLike).where(TweetLike.tweet_id == tweet_id)))
            .scalars()
            .all()
        )
        comment_count = len(
            (
                await db.execute(
                    select(Comment).where(
                        Comment.tweet_id == tweet_id,
                        Comment.parent_comment_id.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        share_count = len(
            (await db.execute(select(Share).where(Share.tweet_id == tweet_id)))
            .scalars()
            .all()
        )
        bookmark_count = len(
            (await db.execute(select(Bookmark).where(Bookmark.tweet_id == tweet_id)))
            .scalars()
            .all()
        )
        is_liked = (
            await db.execute(
                select(TweetLike).where(
                    TweetLike.tweet_id == tweet_id, TweetLike.user_id == user_id
                )
            )
        ).scalar_one_or_none() is not None
        is_bookmarked = (
            await db.execute(
                select(Bookmark).where(
                    Bookmark.tweet_id == tweet_id, Bookmark.user_id == user_id
                )
            )
        ).scalar_one_or_none() is not None
        is_shared = (
            await db.execute(
                select(Share).where(
                    Share.tweet_id == tweet_id, Share.user_id == user_id
                )
            )
        ).scalar_one_or_none() is not None
        media_items = (
            (
                await db.execute(
                    select(TweetMedia).where(TweetMedia.tweet_id == tweet_id)
                )
            )
            .scalars()
            .all()
        )
        media_responses = [
            TweetMediaResponse(
                media_type=m.media_type,
                media_path=m.media_path,
            )
            for m in media_items
        ]
        comments, _ = await self.get_comments(db, tweet_id, user_id, page=1)
        comment_responses = comments[:2]
        response = TweetResponse(
            id=tweet.id,
            user_id=tweet.user_id,
            text=tweet.text,
            media=media_responses,
            view_count=tweet.view_count or 0,
            like_count=like_count,
            comment_count=comment_count,
            share_count=share_count,
            bookmark_count=bookmark_count,
            is_shared=is_shared,
            is_liked=is_liked,
            is_bookmarked=is_bookmarked,
            created_at=tweet.created_at,
            edited_at=tweet.edited_at,
            comments=comment_responses,
            user_name=profile.name if profile else "Unknown User",
            photo=(
                profile.photo_path
                if profile and profile.photo_path and profile.photo_content_type
                else None
            ),
            is_organizational=profile.is_organizational if profile else False,
            is_prime=profile.is_prime if profile else False,
        )
        await cache_service.set(cache_key, response.model_dump(), ttl=300)
        return response

    async def get_feed_user_ids(self, db: AsyncSession, user_id: str) -> list:
        following_rows = (
            (
                await db.execute(
                    select(Follower.followee_id).where(Follower.follower_id == user_id)
                )
            )
            .scalars()
            .all()
        )
        user_ids = {user_id}
        if following_rows:
            profiles = (
                await db.execute(
                    select(User, UserProfile)
                    .join(UserProfile, User.user_id == UserProfile.user_id)
                    .where(User.user_id.in_(following_rows))
                )
            ).all()
            for user, profile in profiles:
                if profile.is_organizational or not user.is_private:
                    user_ids.add(user.user_id)
                elif user.is_private:
                    is_follower = await db.execute(
                        select(Follower).where(
                            Follower.follower_id == user_id,
                            Follower.followee_id == user.user_id,
                        )
                    )
                    if is_follower.scalar_one_or_none():
                        user_ids.add(user.user_id)
        return list(user_ids)

    async def filter_tweets_privacy(
        self, db: AsyncSession, tweets, current_user_id: str
    ):
        filtered = []
        for t in tweets:
            profile = await user_profile_service.get_user_profile(
                db, t.user_id, current_user_id
            )
            can_view = profile.can_view_content
            if not profile.is_private:
                can_view = True
            if profile.is_organizational or can_view:
                filtered.append(t)
        return filtered

    async def get_merged_feed(
        self,
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        include_recommendations: bool = True,
        last_tweet_id: int = None,
        refresh: bool = False,
        feed_type: str = "latest", 
    ) -> TweetFeedResponse:
        """
        Get a merged feed including user's following tweets and recommendations
        with advanced caching, optimization, and analytics
        """
        feed_cache_key = f"twitter_feed:{user_id}:p{page}:s{page_size}:inc{include_recommendations}:type{feed_type}:last{last_tweet_id or 0}"
        
        if not refresh:
            try:
                # Use cache_with_lock to prevent cache stampede
                async def compute_feed():
                    result = await self._compute_merged_feed_internal(
                        db, user_id, page, page_size, include_recommendations, 
                        last_tweet_id, feed_type, refresh
                    )
                    # Return the dictionary representation for caching
                    return result.model_dump()
                
                cached_result = await cache_service.cache_with_lock(
                    feed_cache_key, 
                    compute_feed, 
                    ttl=600,  # 10 minutes
                    lock_ttl=30  # 30 seconds lock
                )
                
                if cached_result:
                    return TweetFeedResponse(**cached_result)
                    
            except Exception as e:
                logger.warning(f"Cache with lock failed for feed {user_id}: {e}")
                # Fallback to direct computation
                pass
        
        # Direct computation if refresh=True or cache fails
        return await self._compute_merged_feed_internal(
            db, user_id, page, page_size, include_recommendations, 
            last_tweet_id, feed_type, refresh
        )

    async def _compute_merged_feed_internal(
        self,
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        include_recommendations: bool = True,
        last_tweet_id: int = None,
        feed_type: str = "latest",
        refresh: bool = False,  # Add refresh parameter
    ) -> TweetFeedResponse:
        """Internal method for computing merged feed - original logic moved here"""
        feed_cache_key = f"twitter_feed:{user_id}:p{page}:s{page_size}:inc{include_recommendations}:type{feed_type}:last{last_tweet_id or 0}"
        
        cached = await cache_service.get(feed_cache_key)
        if cached:
            logger.info(json.dumps({"event": "cache_hit", "key": feed_cache_key, "type": "twitter_feed"}))
            return TweetFeedResponse(**cached)

        logger.info(json.dumps({"event": "cache_miss", "key": feed_cache_key, "type": "twitter_feed"}))

        query_timeout = 5.0
        

        if feed_type == "latest":
            # Fresh tweets from last 24 hours
            time_cutoff = datetime.now() - timedelta(hours=24)
            cache_key_suffix = f"latest_24h"
        else:
            time_cutoff = datetime.now() - timedelta(days=30)
            cache_key_suffix = f"older_scroll"
        

        current_time = datetime.now()
        if refresh:
    
            cache_timestamp = current_time.strftime("%Y%m%d%H%M%S")
        else:
    
            if feed_type == "latest":
                cache_timestamp = current_time.strftime("%Y%m%d%H")
            else:
                cache_timestamp = current_time.strftime("%Y%m%d%H%M")[:-1] + "0"
        
        base_cache_key = f"twitter_feed:{user_id}:p{page}:r{include_recommendations}:{feed_type}"
        feed_cache_key = f"{base_cache_key}:{cache_key_suffix}:{cache_timestamp}"
        

        if last_tweet_id:
            feed_cache_key += f":after{last_tweet_id}"
        
        try:
            cached = await cache_service.get(feed_cache_key)
            if cached:
                logger.info(f"✅ L1 Cache hit: {feed_cache_key}")
                return TweetFeedResponse(**cached)
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
        
        logger.info(f"🔄 Building prioritized feed for user {user_id}, page {page}")

        @asynccontextmanager
        async def query_with_timeout(query_name: str):
            try:
                start_time = datetime.now()
                yield
                duration = (datetime.now() - start_time).total_seconds()
                if duration > query_timeout:
                    logger.warning(f"⚠️  Slow query {query_name}: {duration:.2f}s")
            except asyncio.TimeoutError:
                logger.error(f"❌ Query timeout: {query_name}")
                raise InternalServerError(f"Database query timeout: {query_name}")

        try:
            # Get current hour for cache optimization
            current_hour = datetime.now().hour
            
            # Get following users
            following_cache_key = f"following_optimized:{user_id}:h{current_hour}"
            following_ids = await cache_service.get(following_cache_key) if not refresh else None
            if not following_ids:
                async with query_with_timeout("get_following"):
                    following_query = (
                        select(Follower.followee_id)
                        .where(Follower.follower_id == user_id)
                        .limit(5000)
                    )
                    following_result = await asyncio.wait_for(
                        db.execute(following_query), timeout=query_timeout
                    )
                    following_ids = list(following_result.scalars().all())
                    await cache_service.set(
                        following_cache_key, following_ids, ttl=3600
                    )
            following_set = set(following_ids)

            all_user_metadata_key = f"all_user_metadata:h{current_hour}"
            all_user_metadata = await cache_service.get(all_user_metadata_key) if not refresh else None
            if not all_user_metadata:
                async with query_with_timeout("get_all_user_metadata"):
                    # Get organizational prime users (they can't be private)
                    org_prime_query = (
                        select(
                            User.user_id,
                            User.is_private,
                            User.is_blocked,
                            UserProfile.name,
                            UserProfile.photo_path,
                            UserProfile.is_organizational,
                            UserProfile.is_prime,
                        )
                        .select_from(
                            User.__table__.join(
                                UserProfile.__table__,
                                User.user_id == UserProfile.user_id,
                            )
                        )
                        .where(
                            and_(
                                UserProfile.is_organizational == True,
                                UserProfile.is_prime == True,
                                User.is_blocked == False
                            )
                        )
                        .limit(1000)
                    )
                    
                    # Get following users metadata
                    following_metadata_query = (
                        select(
                            User.user_id,
                            User.is_private,
                            User.is_blocked,
                            UserProfile.name,
                            UserProfile.photo_path,
                            UserProfile.is_organizational,
                            UserProfile.is_prime,
                        )
                        .select_from(
                            User.__table__.join(
                                UserProfile.__table__,
                                User.user_id == UserProfile.user_id,
                            )
                        )
                        .where(User.user_id.in_(following_ids[:1000]))
                    )
                    
                    org_prime_result, following_result = await asyncio.gather(
                        asyncio.wait_for(db.execute(org_prime_query), timeout=query_timeout),
                        asyncio.wait_for(db.execute(following_metadata_query), timeout=query_timeout)
                    )
                    
                    all_user_metadata = {}
                    # Add organizational prime users
                    for row in org_prime_result:
                        all_user_metadata[row.user_id] = {
                            "is_private": row.is_private,
                            "is_blocked": row.is_blocked,
                            "name": row.name,
                            "photo": row.photo_path,
                            "is_organizational": row.is_organizational,
                            "is_prime": row.is_prime,
                        }
                    
                    # Add following users (override if already exists)
                    for row in following_result:
                        all_user_metadata[row.user_id] = {
                            "is_private": row.is_private,
                            "is_blocked": row.is_blocked,
                            "name": row.name,
                            "photo": row.photo_path,
                            "is_organizational": row.is_organizational,
                            "is_prime": row.is_prime,
                        }
                    
                    await cache_service.set(all_user_metadata_key, all_user_metadata, ttl=1800)
            valid_user_ids = [
                uid for uid, metadata in all_user_metadata.items()
                if not metadata.get("is_blocked", False) and uid != user_id
            ]

            # Debug log for refresh operations
            if refresh:
                logger.info(f"🔄 Refresh debug - user_id: {user_id}, following_ids: {len(following_ids)}, valid_user_ids: {len(valid_user_ids)}, include_recommendations: {include_recommendations}")

            # Ensure we have users to query from, especially for recommendations during refresh
            fallback_user_ids = []  # Initialize to avoid scope issues
            if not valid_user_ids and include_recommendations:
                # Fallback: get some active users for recommendations during refresh
                async with query_with_timeout("get_fallback_users"):
                    fallback_query = (
                        select(User.user_id)
                        .where(
                            and_(
                                User.is_blocked == False,
                                User.user_id != user_id
                            )
                        )
                        .limit(100)
                    )
                    fallback_result = await asyncio.wait_for(
                        db.execute(fallback_query), timeout=query_timeout
                    )
                    fallback_user_ids = [row[0] for row in fallback_result.all()]
                    if fallback_user_ids:
                        # Get metadata for fallback users
                        fallback_metadata_query = (
                            select(
                                User.user_id,
                                User.is_private,
                                User.is_blocked,
                                UserProfile.name,
                                UserProfile.photo_path,
                                UserProfile.is_organizational,
                                UserProfile.is_prime,
                            )
                            .select_from(
                                User.__table__.join(
                                    UserProfile.__table__,
                                    User.user_id == UserProfile.user_id,
                                )
                            )
                            .where(User.user_id.in_(fallback_user_ids))
                        )
                        fallback_metadata_result = await asyncio.wait_for(
                            db.execute(fallback_metadata_query), timeout=query_timeout
                        )
                        
                        # Add fallback users to metadata
                        for row in fallback_metadata_result:
                            all_user_metadata[row.user_id] = {
                                "is_private": row.is_private,
                                "is_blocked": row.is_blocked,
                                "name": row.name,
                                "photo": row.photo_path,
                                "is_organizational": row.is_organizational,
                                "is_prime": row.is_prime,
                            }
                        
                        logger.info(f"🔄 Added {len(fallback_user_ids)} fallback users for recommendations refresh")
                        
            valid_user_ids = [
                uid for uid, metadata in all_user_metadata.items()
                            if not metadata.get("is_blocked", False) and uid != user_id
            ]

            # Build tweet query conditions based on feed type
            base_tweet_conditions = [
                Tweet.user_id.in_(valid_user_ids[:2000]),
            ]
            
            # Time-based filtering
            if feed_type == "latest":
                # Fresh tweets from last 24 hours
                base_tweet_conditions.append(Tweet.created_at >= time_cutoff)
            else:
                # Older tweets for infinite scroll
                if last_tweet_id:
                    # Get tweets older than the last_tweet_id
                    base_tweet_conditions.append(Tweet.id < last_tweet_id)
                else:
                    # Get tweets older than 24 hours
                    base_tweet_conditions.append(Tweet.created_at < (datetime.now() - timedelta(hours=24)))
            
            async with query_with_timeout("get_all_feed_candidates"):
                # Adjust query limit based on feed type
                query_limit = 2000 if feed_type == "latest" else 1000
                
                tweets_query = (
                    select(
                        Tweet.id,
                        Tweet.user_id,
                        Tweet.text,
                        Tweet.view_count,
                        Tweet.created_at,
                        Tweet.edited_at,
                    )
                    .where(and_(*base_tweet_conditions))
                    .order_by(desc(Tweet.created_at))
                    .limit(query_limit)
                )
                tweets_result = await asyncio.wait_for(
                    db.execute(tweets_query), timeout=query_timeout
                )
                all_tweets = tweets_result.fetchall()
            
            if not all_tweets:
                # Provide better feedback during refresh
                if refresh:
                    logger.warning(f"🔄 No tweets found during refresh for user {user_id} - valid_user_ids: {len(valid_user_ids)}, include_recommendations: {include_recommendations}")
                
                empty_feed = TweetFeedResponse(
                    tweets=[], total=0, page=page, page_size=page_size,
                    refresh_timestamp=datetime.now().isoformat() if refresh else None,
                )
                # Shorter cache TTL for empty feeds during refresh
                cache_ttl = 30 if refresh else 60
                await cache_service.set(feed_cache_key, empty_feed.model_dump(), ttl=cache_ttl)
                return empty_feed
            
            tweet_ids = [t.id for t in all_tweets]

            # Get engagement data, user flags, and media data
            async def get_engagement_counts():
                # More specific cache key to avoid collisions
                tweet_ids_str = ','.join(map(str, sorted(tweet_ids)))
                engagement_cache_key = f"engagement_batch:{user_id}:{hashlib.md5(tweet_ids_str.encode()).hexdigest()[:12]}"
                cached_engagement = await cache_service.get(engagement_cache_key) if not refresh else None
                if cached_engagement and isinstance(cached_engagement, dict) and len(cached_engagement) > 0:
                    # Validate cached data - ensure it has the expected structure
                    sample_key = next(iter(cached_engagement.keys()))
                    if isinstance(cached_engagement[sample_key], dict) and 'likes' in cached_engagement[sample_key]:
                        return cached_engagement
                
                async with query_with_timeout("get_engagement_counts"):
                    likes_query = (
                        select(
                            TweetLike.tweet_id,
                            func.count(TweetLike.tweet_id).label("count"),
                        )
                        .where(TweetLike.tweet_id.in_(tweet_ids))
                        .group_by(TweetLike.tweet_id)
                    )
                    comments_query = (
                        select(Comment.tweet_id, func.count(Comment.id).label("count"))
                        .where(
                            Comment.tweet_id.in_(tweet_ids),
                            Comment.parent_comment_id.is_(None),
                        )
                        .group_by(Comment.tweet_id)
                    )
                    shares_query = (
                        select(
                            Share.tweet_id, func.count(Share.tweet_id).label("count")
                        )
                        .where(Share.tweet_id.in_(tweet_ids))
                        .group_by(Share.tweet_id)
                    )
                    bookmarks_query = (
                        select(
                            Bookmark.tweet_id,
                            func.count(Bookmark.tweet_id).label("count"),
                        )
                        .where(Bookmark.tweet_id.in_(tweet_ids))
                        .group_by(Bookmark.tweet_id)
                    )
                    
                    likes_result, comments_result, shares_result, bookmarks_result = (
                        await asyncio.gather(
                            asyncio.wait_for(db.execute(likes_query), timeout=query_timeout),
                            asyncio.wait_for(db.execute(comments_query), timeout=query_timeout),
                            asyncio.wait_for(db.execute(shares_query), timeout=query_timeout),
                            asyncio.wait_for(db.execute(bookmarks_query), timeout=query_timeout),
                        )
                    )
                    
                    engagement = {
                        tweet_id: {
                            "likes": 0,
                            "comments": 0,
                            "shares": 0,
                            "bookmarks": 0,
                        }
                        for tweet_id in tweet_ids
                    }
                    
                    for row in likes_result:
                        engagement[row.tweet_id]["likes"] = row.count  # type: ignore
                    for row in comments_result:
                        engagement[row.tweet_id]["comments"] = row.count  # type: ignore
                    for row in shares_result:
                        engagement[row.tweet_id]["shares"] = row.count  # type: ignore
                    for row in bookmarks_result:
                        engagement[row.tweet_id]["bookmarks"] = row.count  # type: ignore
                    
                    # Only cache if we have valid data
                    if engagement and len(engagement) > 0:
                        await cache_service.set(engagement_cache_key, engagement, ttl=600)
                    return engagement

            async def get_user_flags():
                tweet_ids_str = ','.join(map(str, sorted(tweet_ids)))
                flags_cache_key = f"user_flags:{user_id}:{hashlib.md5(tweet_ids_str.encode()).hexdigest()[:12]}"
                cached_flags = await cache_service.get(flags_cache_key) if not refresh else None
                if cached_flags and isinstance(cached_flags, dict):
                    # Convert lists back to sets for internal use
                    return {
                        "liked": set(cached_flags.get("liked", [])),
                        "bookmarked": set(cached_flags.get("bookmarked", [])),
                    }
                
                async with query_with_timeout("get_user_flags"):
                    user_likes_query = select(TweetLike.tweet_id).where(
                        TweetLike.tweet_id.in_(tweet_ids), TweetLike.user_id == user_id
                    )
                    user_bookmarks_query = select(Bookmark.tweet_id).where(
                        Bookmark.tweet_id.in_(tweet_ids), Bookmark.user_id == user_id
                    )
                    
                    likes_result, bookmarks_result = await asyncio.gather(
                        asyncio.wait_for(db.execute(user_likes_query), timeout=query_timeout),
                        asyncio.wait_for(db.execute(user_bookmarks_query), timeout=query_timeout),
                    )
                    
                    user_flags = {
                        "liked": set(likes_result.scalars().all()),
                        "bookmarked": set(bookmarks_result.scalars().all()),
                    }
                    
                    await cache_service.set(
                        flags_cache_key,
                        {
                            "liked": list(user_flags["liked"]),
                            "bookmarked": list(user_flags["bookmarked"]),
                        },
                        ttl=300,
                    )
                    return user_flags

            async def get_media_data():
                tweet_ids_str = ','.join(map(str, sorted(tweet_ids)))
                media_cache_key = f"media_batch:{user_id}:{hashlib.md5(tweet_ids_str.encode()).hexdigest()[:12]}"
                cached_media = await cache_service.get(media_cache_key) if not refresh else None
                if cached_media and isinstance(cached_media, dict):
                    return cached_media
                
                async with query_with_timeout("get_media_data"):
                    media_query = select(TweetMedia).where(
                        TweetMedia.tweet_id.in_(tweet_ids)
                    )
                    media_result = await asyncio.wait_for(
                        db.execute(media_query), timeout=query_timeout
                    )
                    
                    media_dict = {}
                    for media in media_result.scalars().all():
                        if media.tweet_id not in media_dict:  # type: ignore
                            media_dict[media.tweet_id] = []  # type: ignore
                        media_dict[media.tweet_id].append({  # type: ignore
                            "media_type": media.media_type,  # type: ignore
                            "media_path": media.media_path,  # type: ignore
                        })
                    
                    await cache_service.set(media_cache_key, media_dict, ttl=1800)
                    return media_dict

            # Use batch cache operations for better performance
            tweet_ids_str = ','.join(map(str, sorted(tweet_ids)))
            batch_cache_keys = {
                'engagement': f"engagement_batch:{user_id}:{hashlib.md5(tweet_ids_str.encode()).hexdigest()[:12]}",
                'flags': f"user_flags:{user_id}:{hashlib.md5(tweet_ids_str.encode()).hexdigest()[:12]}",
                'media': f"media_batch:{user_id}:{hashlib.md5(tweet_ids_str.encode()).hexdigest()[:12]}"
            }
            
            batch_cached_data = await cache_service.batch_get(list(batch_cache_keys.values())) if not refresh else {}
            
            # Use batch operations when possible, fallback to individual operations
            async def get_engagement_or_cached():
                if batch_cache_keys['engagement'] in batch_cached_data:
                    return batch_cached_data[batch_cache_keys['engagement']]
                return await get_engagement_counts()
                
            async def get_flags_or_cached():
                if batch_cache_keys['flags'] in batch_cached_data:
                    cached_flags = batch_cached_data[batch_cache_keys['flags']]
                    if isinstance(cached_flags, dict):
                        # Convert lists back to sets for internal use
                        return {
                            "liked": set(cached_flags.get("liked", [])),
                            "bookmarked": set(cached_flags.get("bookmarked", [])),
                        }
                return await get_user_flags()
                
            async def get_media_or_cached():
                if batch_cache_keys['media'] in batch_cached_data:
                    return batch_cached_data[batch_cache_keys['media']]
                return await get_media_data()

            engagement_data, user_flags, media_dict = await asyncio.gather(
                get_engagement_or_cached(),
                get_flags_or_cached(), 
                get_media_or_cached()
            )

            # Validate gathered data to prevent null issues
            if not isinstance(engagement_data, dict):
                logger.warning(f"Invalid engagement_data type: {type(engagement_data)}")
                engagement_data = {}
            
            if not isinstance(user_flags, dict):
                logger.warning(f"Invalid user_flags type: {type(user_flags)}")
                user_flags = {"liked": set(), "bookmarked": set()}
            
            if not isinstance(media_dict, dict):
                logger.warning(f"Invalid media_dict type: {type(media_dict)}")
                media_dict = {}
            
            # Validate user metadata
            if not isinstance(all_user_metadata, dict):
                logger.warning(f"Invalid all_user_metadata type: {type(all_user_metadata)}")
                all_user_metadata = {}
            
            # Debug log user metadata status
            if refresh:
                logger.info(f"🔄 User metadata debug - total users: {len(all_user_metadata)}, user_id: {user_id}")

            # Twitter-style real-time engagement velocity tracking
            async def get_engagement_velocity(tweet_ids):
                # Use all tweet IDs, not just first 100, and add user_id for uniqueness
                tweet_ids_str = ','.join(map(str, sorted(tweet_ids)))
                velocity_cache_key = f"engagement_velocity:{user_id}:{hashlib.md5(tweet_ids_str.encode()).hexdigest()[:12]}"
                cached_velocity = await cache_service.get(velocity_cache_key) if not refresh else None
                
                if cached_velocity and isinstance(cached_velocity, dict) and len(cached_velocity) > 0:
                    return cached_velocity
                
                try:
                    current_time = datetime.now()
                    recent_cutoff = current_time - timedelta(minutes=30)
                    previous_cutoff = current_time - timedelta(hours=1)
                    
                    recent_likes = await db.execute(
                        select(TweetLike.tweet_id, func.count().label('count'))
                        .where(
                            and_(
                                TweetLike.tweet_id.in_(tweet_ids),
                                TweetLike.created_at >= recent_cutoff
                            )
                        )
                        .group_by(TweetLike.tweet_id)
                    )
                    
                    previous_likes = await db.execute(
                        select(TweetLike.tweet_id, func.count().label('count'))
                        .where(
                            and_(
                                TweetLike.tweet_id.in_(tweet_ids),
                                TweetLike.created_at >= previous_cutoff,
                                TweetLike.created_at < recent_cutoff
                            )
                        )
                        .group_by(TweetLike.tweet_id)
                    )
                    
                    recent_counts = {row.tweet_id: row.count for row in recent_likes}
                    previous_counts = {row.tweet_id: row.count for row in previous_likes}
                    
                    velocity_scores = {}
                    for tweet_id in tweet_ids:
                        recent = recent_counts.get(tweet_id, 0)
                        previous = previous_counts.get(tweet_id, 0)
                        
                        velocity = (recent - previous) / max(previous, 1) if previous > 0 else recent
                        velocity_scores[tweet_id] = max(0, velocity)
                    
                    # Only cache if we have valid data
                    if velocity_scores and len(velocity_scores) > 0:
                        await cache_service.set(velocity_cache_key, velocity_scores, ttl=60)
                    return velocity_scores
                    
                except Exception as e:
                    logger.warning(f"Failed to calculate engagement velocity: {e}")
                    return {tweet_id: 0 for tweet_id in tweet_ids}

            # Get engagement velocity for trending detection
            engagement_velocity = await get_engagement_velocity(tweet_ids)

            # Update the advanced scoring to include velocity
            def calculate_twitter_style_score(eng, tweet_created_at, tweet_id, user_affinity=0):
                hours_old = (datetime.now() - tweet_created_at).total_seconds() / 3600
                
                base_score = (
                    eng.get("likes", 0) * 3
                    + eng.get("shares", 0) * 4
                    + eng.get("bookmarks", 0) * 2
                    + eng.get("comments", 0) * 2
                    + (eng.get("views", 0) or 0) * 0.1
                )
                
                if base_score > 50:
                    decay_window = 72
                elif base_score > 20:
                    decay_window = 48
                elif base_score > 5:
                    decay_window = 24
                else:
                    decay_window = 12
                
                time_decay = max(0.1, 1.0 - (hours_old / decay_window))
                velocity_bonus = engagement_velocity.get(tweet_id, 0) * 10
                affinity_bonus = user_affinity * base_score * 0.5
                diversity_penalty = 1.0 - (user_affinity * 0.3) if user_affinity > 0.8 else 1.0
                
                final_score = (base_score * time_decay + velocity_bonus + affinity_bonus) * diversity_penalty
                return max(0, final_score)

            # Enhanced priority category with user interaction history
            def get_enhanced_priority_category(tweet_row, metadata, engagement, user_interaction_signals):
                is_org = metadata.get("is_organizational", False)
                is_prime = metadata.get("is_prime", False)
                is_following = tweet_row.user_id in following_set
                
                has_high_engagement = (
                    engagement.get("likes", 0) >= 5
                    or engagement.get("shares", 0) >= 2
                    or engagement.get("bookmarks", 0) >= 3
                    or engagement.get("comments", 0) >= 2
                    or (tweet_row.view_count or 0) >= 100
                )
                
                has_any_engagement = (
                    engagement.get("likes", 0) > 0
                    or engagement.get("shares", 0) > 0
                    or engagement.get("bookmarks", 0) > 0
                    or engagement.get("comments", 0) > 0
                    or (tweet_row.view_count or 0) > 0
                )
                
                user_affinity = user_interaction_signals.get(tweet_row.user_id, 0)
                
                if is_prime and is_org and has_high_engagement:
                    return "prime_org_high_engagement"
                elif is_prime and is_org and has_any_engagement:
                    return "prime_org_medium_engagement"
                elif is_prime and is_org:
                    return "prime_org_no_engagement"
                elif is_following and user_affinity > 0.7 and has_any_engagement:
                    return "high_affinity_following"
                elif is_following and has_high_engagement:
                    return "following_high_engagement"
                elif is_following and has_any_engagement:
                    return "following_medium_engagement"
                elif is_following:
                    return "following_no_engagement"
                elif has_high_engagement and user_affinity > 0.3:
                    return "trending_relevant"
                elif has_high_engagement:
                    return "trending_general"
                else:
                    return "other"

            # Simplified user interaction signals (like Twitter's ML models)
            async def get_user_interaction_signals(user_id, valid_user_ids):
                signals_cache_key = f"user_interaction_signals:{user_id}:h{current_hour}"
                
                if refresh:
                    cached_signals = None
                    ttl = 900
                else:
                    cached_signals = await cache_service.get(signals_cache_key)
                    ttl = 3600
                
                if cached_signals:
                    return cached_signals
                
                recent_interactions_query = select(
                    TweetLike.user_id.label('interacted_with'),
                    func.count().label('interaction_count')
                ).select_from(
                    TweetLike.__table__.join(Tweet.__table__, TweetLike.tweet_id == Tweet.id)
                ).where(
                    and_(
                        TweetLike.user_id == user_id,
                        Tweet.created_at >= datetime.now() - timedelta(days=7),
                        Tweet.user_id.in_(valid_user_ids[:1000])
                    )
                ).group_by(Tweet.user_id).limit(100)
                
                try:
                    result = await db.execute(recent_interactions_query)
                    interactions = result.fetchall()
                    
                    max_interactions = max([r.interaction_count for r in interactions], default=1)
                    signals = {
                        r.interacted_with: min(1.0, r.interaction_count / max_interactions)
                        for r in interactions
                    }
                    
                    await cache_service.set(signals_cache_key, signals, ttl=ttl)
                    return signals
                    
                except Exception as e:
                    logger.warning(f"Failed to get interaction signals: {e}")
                    return {}

            # Get user interaction signals
            user_interaction_signals = await get_user_interaction_signals(user_id, valid_user_ids)

            # Enhanced categorization
            enhanced_categorized_tweets = {
                "prime_org_high_engagement": [],
                "prime_org_medium_engagement": [],
                "prime_org_no_engagement": [],
                "high_affinity_following": [],
                "following_high_engagement": [],
                "following_medium_engagement": [],
                "following_no_engagement": [],
                "trending_relevant": [],
                "trending_general": [],
                "other": [],
            }

            # Get missing user metadata for tweets from users not in cache
            missing_user_ids = []
            for tweet_row in all_tweets:
                if tweet_row.user_id not in all_user_metadata:
                    missing_user_ids.append(tweet_row.user_id)
            
            # Fetch missing user metadata if any
            if missing_user_ids:
                logger.info(f"🔄 Fetching metadata for {len(missing_user_ids)} missing users")
                async with query_with_timeout("get_missing_user_metadata"):
                    missing_metadata_query = (
                        select(
                            User.user_id,
                            User.is_private,
                            User.is_blocked,
                            UserProfile.name,
                            UserProfile.photo_path,
                            UserProfile.is_organizational,
                            UserProfile.is_prime,
                        )
                        .select_from(
                            User.__table__.join(
                                UserProfile.__table__,
                                User.user_id == UserProfile.user_id,
                            )
                        )
                        .where(User.user_id.in_(missing_user_ids))
                    )
                    missing_result = await asyncio.wait_for(
                        db.execute(missing_metadata_query), timeout=query_timeout
                    )
                    
                    # Add missing users to metadata
                    for row in missing_result:
                        all_user_metadata[row.user_id] = {
                            "is_private": row.is_private,
                            "is_blocked": row.is_blocked,
                            "name": row.name,
                            "photo": row.photo_path,
                            "is_organizational": row.is_organizational,
                            "is_prime": row.is_prime,
            }

            for tweet_row in all_tweets:
                metadata = all_user_metadata.get(tweet_row.user_id, {})
                engagement = engagement_data.get(tweet_row.id, {})
                category = get_enhanced_priority_category(tweet_row, metadata, engagement, user_interaction_signals)
                
                if category in enhanced_categorized_tweets:
                    # Use advanced scoring with time decay
                    score = calculate_twitter_style_score(engagement, tweet_row.created_at, tweet_row.id, user_interaction_signals.get(tweet_row.user_id, 0))
                    enhanced_categorized_tweets[category].append({
                        "tweet_row": tweet_row,
                        "metadata": metadata,
                        "engagement": engagement,
                        "score": score
                    })

            # Sort each category by enhanced score
            for category in enhanced_categorized_tweets:
                enhanced_categorized_tweets[category].sort(key=lambda x: x["score"], reverse=True)

            enhanced_category_limits = {
                "prime_org_high_engagement": int(page_size * 0.32),
                "prime_org_medium_engagement": int(page_size * 0.18),
                "prime_org_no_engagement": int(page_size * 0.12),
                "high_affinity_following": int(page_size * 0.18),
                "following_high_engagement": int(page_size * 0.08),
                "following_medium_engagement": int(page_size * 0.07),
                "following_no_engagement": int(page_size * 0.03),
                "trending_relevant": int(page_size * 0.01),
                "trending_general": int(page_size * 0.01),
            }

            def inject_diversity(categorized_tweets, user_id):
                diverse_tweets = []
                
                if "other" in categorized_tweets:
                    diversity_count = max(2, int(page_size * 0.12))
                    trending_others = sorted(
                        categorized_tweets["other"][:100],
                        key=lambda x: x["score"], 
                        reverse=True
                    )[:diversity_count]
                    diverse_tweets.extend(trending_others)
                
                return diverse_tweets

            diversity_tweets = inject_diversity(enhanced_categorized_tweets, user_id)

            selected_tweets = []
            for category, limit in enhanced_category_limits.items():
                available_tweets = enhanced_categorized_tweets[category]
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                selected_tweets.extend(available_tweets[start_idx:end_idx])

            remaining_space = page_size - len(selected_tweets)
            if remaining_space > 0 and diversity_tweets:
                selected_tweets.extend(diversity_tweets[:remaining_space])
            if len(selected_tweets) < page_size:
                remaining_needed = page_size - len(selected_tweets)
                all_remaining = []
                
                for category in enhanced_categorized_tweets:
                    if category not in enhanced_category_limits:
                        continue
                    limit = enhanced_category_limits[category]
                    start_idx = (page - 1) * limit + limit
                    all_remaining.extend(enhanced_categorized_tweets[category][start_idx:])
                
                # Sort remaining by score and take what we need
                all_remaining.sort(key=lambda x: x["score"], reverse=True)
                selected_tweets.extend(all_remaining[:remaining_needed])

            # Use the enhanced categorization for the response
            categorized_tweets = enhanced_categorized_tweets

            # Convert to response format
            tweet_responses = []
            for tweet_data in selected_tweets:
                tweet_row = tweet_data["tweet_row"]
                metadata = tweet_data.get("metadata", {})
                engagement = tweet_data.get("engagement", {})
                
                # Validate metadata to prevent null issues
                if not isinstance(metadata, dict):
                    metadata = {}
                    
                # Validate engagement data to prevent null/0 issues
                if not isinstance(engagement, dict):
                    engagement = {}
                
                # Ensure engagement counts are non-negative integers
                safe_engagement = {
                    "likes": max(0, engagement.get("likes", 0) or 0),
                    "comments": max(0, engagement.get("comments", 0) or 0),
                    "shares": max(0, engagement.get("shares", 0) or 0),
                    "bookmarks": max(0, engagement.get("bookmarks", 0) or 0),
                }
                
                # Validate user_flags to prevent null issues
                safe_user_flags = {
                    "liked": user_flags.get("liked", set()) if isinstance(user_flags, dict) else set(),
                    "bookmarked": user_flags.get("bookmarked", set()) if isinstance(user_flags, dict) else set(),
                }
                
                media_items = [
                    TweetMediaResponse(
                        media_type=m["media_type"], media_path=m["media_path"]  # type: ignore
                    )
                    for m in media_dict.get(tweet_row.id, []) if isinstance(media_dict, dict)
                ]
                
                response = TweetResponse(
                    id=tweet_row.id,  # type: ignore
                    user_id=tweet_row.user_id,  # type: ignore
                    text=tweet_row.text,  # type: ignore
                    media=media_items,
                    view_count=tweet_row.view_count or 0,  # type: ignore
                    like_count=safe_engagement["likes"],
                    comment_count=safe_engagement["comments"],
                    share_count=safe_engagement["shares"],
                    bookmark_count=safe_engagement["bookmarks"],
                    is_shared=False,
                    is_liked=tweet_row.id in safe_user_flags["liked"],  # type: ignore
                    is_bookmarked=tweet_row.id in safe_user_flags["bookmarked"],  # type: ignore
                    created_at=tweet_row.created_at,  # type: ignore
                    edited_at=tweet_row.edited_at,  # type: ignore
                    comments=[],
                    user_name=metadata.get("name", "Unknown"),
                    photo=metadata.get("photo"),
                    is_organizational=metadata.get("is_organizational", False),
                    is_prime=metadata.get("is_prime", False),
                )
                tweet_responses.append(response)

            # Calculate total for pagination
            total_tweets = sum(len(categorized_tweets[cat]) for cat in categorized_tweets)
            
            # Calculate has_more for infinite scroll
            has_more = False
            if feed_type == "older" and tweet_responses:
                # Check if there are more older tweets
                last_tweet_in_response = min(t.id for t in tweet_responses)
                check_more_query = (
                    select(func.count(Tweet.id))
                    .where(
                        and_(
                            Tweet.id < last_tweet_in_response,
                            Tweet.user_id.in_(valid_user_ids[:500]),  # Smaller check
                            Tweet.created_at >= (datetime.now() - timedelta(days=30))
                        )
                    )
                    .limit(1)
                )
                more_result = await db.execute(check_more_query)
                has_more = more_result.scalar() > 0

            feed = TweetFeedResponse(
                tweets=tweet_responses,
                total=total_tweets,
                page=page,
                page_size=page_size,
                has_more=has_more if feed_type == "older" else None,
                feed_type=feed_type,
                last_tweet_id=tweet_responses[-1].id if tweet_responses else None,
                refresh_timestamp=current_time.isoformat() if refresh else None,
            )
            
            # Dynamic cache TTL based on feed type and refresh
            if refresh:
                cache_ttl = 60  # Short cache for refreshed content
            elif feed_type == "latest":
                cache_ttl = 300 if tweet_responses else 60  # 5 minutes for latest tweets
            else:
                cache_ttl = 1800 if tweet_responses else 300  # 30 minutes for older tweets
                
            lock_key = f"feed_lock:{feed_cache_key}"
            acquired = await cache_service.acquire_lock(lock_key, ttl=10)
            if acquired:
                try:
                    await cache_service.set(feed_cache_key, feed.model_dump(), ttl=cache_ttl)
                finally:
                    await cache_service.release_lock(lock_key)
            else:
                # If lock not acquired, skip cache set to avoid stampede
                pass
            
            logger.info(
                f"✅ Built Twitter-like feed: {len(tweet_responses)} tweets, "
                f"type={feed_type}, page={page}, refresh={refresh}"
                f" - Categories: {[(cat, len(categorized_tweets[cat])) for cat in categorized_tweets]}"
                f" - Time range: {time_cutoff.strftime('%Y-%m-%d %H:%M')} to now"
                f" - Has more: {has_more if feed_type == 'older' else 'N/A'}"
            )
            
            return feed
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Feed generation timeout for user {user_id}")
            raise InternalServerError("Feed generation timeout - please try again")
        except Exception as e:
            logger.error(f"❌ Error in prioritized get_merged_feed: {str(e)}")
            try:
                fallback_key = f"{base_cache_key}:fallback"
                fallback = await cache_service.get(fallback_key)
                if fallback:
                    logger.info(f"🔄 Using fallback cache for user {user_id}")
                    return TweetFeedResponse(**fallback)
            except Exception:
                pass
            raise InternalServerError(f"Failed to fetch feed: {str(e)}")

    async def get_tweet_feed(
        self, db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
    ) -> TweetFeedResponse:
        return await self.get_merged_feed(
            db, user_id, page, page_size, include_recommendations=False
        )

    async def get_recommended_tweets(
        self, db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
    ) -> TweetFeedResponse:
        return await self.get_merged_feed(
            db, user_id, page, page_size, include_recommendations=True
        )

    async def like_tweet(
        self, db: AsyncSession, user_id: str, request: LikeTweetRequest
    ) -> ActionResponse:
        await self._check_and_auto_unblock_user(db, user_id)
        tweet = (
            await db.execute(select(Tweet).where(Tweet.id == request.tweet_id))
        ).scalar_one_or_none()
        if not tweet:
            raise NotFoundError("Tweet not found")
        like = (
            await db.execute(
                select(TweetLike).where(
                    TweetLike.tweet_id == request.tweet_id, TweetLike.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        try:
            if request.like:
                if not like:
                    db.add(TweetLike(tweet_id=request.tweet_id, user_id=user_id))
                    await db.commit()
                    # Optimized cache invalidation for like
                    await cache_service.invalidate_engagement_cache(request.tweet_id)
                    await cache_service.invalidate_user_interaction_cache(user_id, "like")
                    await cache_service.invalidate_feed_for_followers(db, tweet.user_id)
                    await cache_service.invalidate_twitter_recommendation_cache()
                return ActionResponse(success=True, message="Tweet liked")
            else:
                if like:
                    await db.delete(like)
                    await db.commit()
                    # Optimized cache invalidation for unlike
                    await cache_service.invalidate_engagement_cache(request.tweet_id)
                    await cache_service.invalidate_user_interaction_cache(user_id, "like")
                    await cache_service.invalidate_feed_for_followers(db, tweet.user_id)
                    await cache_service.invalidate_twitter_recommendation_cache()
                return ActionResponse(success=True, message="Tweet unliked")
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to like/unlike tweet: {e}")
            raise e

    async def bookmark_tweet(
        self, db: AsyncSession, user_id: str, request: BookmarkTweetRequest
    ) -> ActionResponse:
        await self._check_and_auto_unblock_user(db, user_id)
        tweet = (
            await db.execute(select(Tweet).where(Tweet.id == request.tweet_id))
        ).scalar_one_or_none()
        if not tweet:
            raise NotFoundError("Tweet not found")
        bookmark = (
            await db.execute(
                select(Bookmark).where(
                    Bookmark.tweet_id == request.tweet_id, Bookmark.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        try:
            if request.bookmark:
                if not bookmark:
                    db.add(Bookmark(tweet_id=request.tweet_id, user_id=user_id))
                    await db.commit()
                    # Optimized cache invalidation for bookmark
                    await cache_service.invalidate_engagement_cache(request.tweet_id)
                    await cache_service.invalidate_user_interaction_cache(user_id, "bookmark")
                    await cache_service.invalidate_twitter_recommendation_cache()
                return ActionResponse(success=True, message="Tweet bookmarked")
            else:
                if bookmark:
                    await db.delete(bookmark)
                    await db.commit()
                    # Optimized cache invalidation for unbookmark
                    await cache_service.invalidate_engagement_cache(request.tweet_id)
                    await cache_service.invalidate_user_interaction_cache(user_id, "bookmark")
                    await cache_service.invalidate_twitter_recommendation_cache()
                return ActionResponse(success=True, message="Tweet unbookmarked")
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to bookmark/unbookmark tweet: {e}")
            raise e

    async def share_tweet(
        self, db: AsyncSession, user_id: str, request: ShareTweetRequest
    ) -> ActionResponse:
        await self._check_and_auto_unblock_user(db, user_id)
        
        # Validate tweet exists
        tweet = (
            await db.execute(select(Tweet).where(Tweet.id == request.tweet_id))
        ).scalar_one_or_none()
        if not tweet:
            raise NotFoundError("Tweet not found")
        
        # Validate recipients
        if user_id in request.recipient_ids:
            raise ValidationError("You cannot share a tweet to yourself")
        
        # Check if all recipients exist
        recipients_result = await db.execute(
            select(User.user_id).where(User.user_id.in_(request.recipient_ids))
        )
        valid_user_ids = {row[0] for row in recipients_result.all()}
        
        # Check for non-existent recipients
        invalid_recipients = set(request.recipient_ids) - valid_user_ids
        if invalid_recipients:
            raise NotFoundError(f"Recipients not found: {', '.join(invalid_recipients)}")
        
        # Get mutual followers efficiently using batch queries
        # Check who the user follows
        user_following_result = await db.execute(
            select(Follower.followee_id).where(
                Follower.follower_id == user_id,
                Follower.followee_id.in_(request.recipient_ids)
            )
        )
        user_following = {row[0] for row in user_following_result.all()}
        
        # Check who follows the user back
        user_followers_result = await db.execute(
            select(Follower.follower_id).where(
                Follower.followee_id == user_id,
                Follower.follower_id.in_(request.recipient_ids)
            )
        )
        user_followers = {row[0] for row in user_followers_result.all()}
        
        # Find mutual followers (users who both follow and are followed by the user)
        valid_recipients = list(user_following & user_followers)
        
        if not valid_recipients:
            raise ValidationError("No valid recipients found - you can only share tweets with users who mutually follow you")
        
        # Check for existing shares and create new ones
        shares_created = []
        already_shared = []
        try:
            # Check existing shares in batch
            existing_shares_result = await db.execute(
                select(Share.recipient_id).where(
                    Share.tweet_id == request.tweet_id,
                    Share.user_id == user_id,
                    Share.recipient_id.in_(valid_recipients)
            )
        )
            existing_shares = {row[0] for row in existing_shares_result.all()}
            
            # Create new shares for recipients who haven't been shared with
            new_shares = []
            for recipient_id in valid_recipients:
                if recipient_id in existing_shares:
                    already_shared.append(recipient_id)
                else:
                    share = Share(
                        tweet_id=request.tweet_id,
                        user_id=user_id,
                        recipient_id=recipient_id,
                        message=request.message,
                    )
                    new_shares.append(share)
                    shares_created.append(recipient_id)
            
            if new_shares:
                db.add_all(new_shares)
            
            if not shares_created and already_shared:
                return ActionResponse(
                    success=True, 
                    message=f"Tweet already shared with all specified users: {', '.join(already_shared)}"
                )
            
            await db.commit()
            
            # Comprehensive cache invalidation
            await cache_service.invalidate_tweet_share_cache(
                request.tweet_id, user_id, valid_recipients
            )
            
            # Build response message
            message_parts = []
            if shares_created:
                message_parts.append(f"Tweet shared successfully with {len(shares_created)} user(s)")
            if already_shared:
                message_parts.append(f"Already shared with {len(already_shared)} user(s)")
            
            return ActionResponse(success=True, message=". ".join(message_parts))
            
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to share tweet {request.tweet_id} from {user_id} to {valid_recipients}: {e}")
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Unexpected error sharing tweet {request.tweet_id}: {e}")
            raise InternalServerError(f"Failed to share tweet: {str(e)}")

    async def create_tweet_snapshot(
        self, db: AsyncSession, tweet_id: int, user_id: str
    ) -> dict:
        tweet_response = await self.get_tweet_response(db, tweet_id, user_id)
        if not tweet_response:
            return None
        media_items = (
            (
                await db.execute(
                    select(TweetMedia).where(TweetMedia.tweet_id == tweet_id)
                )
            )
            .scalars()
            .all()
        )
        return {
            "tweet_id": tweet_id,
            "author_id": tweet_response.user_id,
            "text": tweet_response.text,
            "created_at": tweet_response.created_at.isoformat(),
            "edited_at": (
                tweet_response.edited_at.isoformat()
                if tweet_response.edited_at
                else None
            ),
            "view_count": tweet_response.view_count,
            "media": [
                {
                    "media_type": m.media_type,
                    "media_path": m.media_path,
                }
                for m in media_items
            ],
        }

    async def create_comment_snapshot(
        self, db: AsyncSession, comment_id: int, user_id: str
    ) -> dict:
        comment = (
            await db.execute(select(Comment).where(Comment.id == comment_id))
        ).scalar_one_or_none()
        if not comment:
            return None
        tweet = (
            await db.execute(select(Tweet).where(Tweet.id == comment.tweet_id))
        ).scalar_one_or_none()
        if not tweet:
            return None
        media_items = (
            (
                await db.execute(
                    select(TweetMedia).where(TweetMedia.tweet_id == tweet.id)
                )
            )
            .scalars()
            .all()
        )
        return {
            "comment": {
                "comment_id": comment.id,
                "author_id": comment.user_id,
                "text": comment.text,
                "created_at": comment.created_at.isoformat(),
                "edited_at": (
                    comment.edited_at.isoformat() if comment.edited_at else None
                ),
                "tweet_id": comment.tweet_id,
            },
            "tweet": {
                "tweet_id": tweet.id,
                "author_id": tweet.user_id,
                "text": tweet.text,
                "created_at": tweet.created_at.isoformat(),
                "media": [
                    {
                        "media_type": m.media_type,
                        "media_path": m.media_path,
                    }
                    for m in media_items
                ],
            },
        }

    async def report_tweet(
        self, db: AsyncSession, user_id: str, request: ReportTweetRequest
    ) -> ActionResponse:
        await self._check_and_auto_unblock_user(db, user_id)
        tweet = (
            await db.execute(select(Tweet).where(Tweet.id == request.tweet_id))
        ).scalar_one_or_none()
        if not tweet:
            raise NotFoundError("Tweet not found")
        if tweet.user_id == user_id:
            raise ValidationError("You cannot report your own tweet.")
        try:
            snapshot = await self.create_tweet_snapshot(db, tweet.id, user_id)
            report = TweetReport(
                tweet_id=request.tweet_id,
                user_id=user_id,
                reason=request.reason,
                snapshot=snapshot,
            )
            db.add(report)
            await db.commit()
            await cache_service.invalidate_engagement_cache(request.tweet_id)
            await cache_service.invalidate_user_activity_cache(user_id, "report")
            return ActionResponse(success=True, message="Tweet reported")
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to report tweet: {e}")
            raise e

    async def comment_on_tweet(
        self, db: AsyncSession, user_id: str, request: CommentTweetRequest
    ) -> CommentResponse:
        await self._check_and_auto_unblock_user(db, user_id)
        if not request.text or not request.text.strip():
            raise ValidationError("Comment text is required")
        if len(request.text) > 280:
            raise ValidationError("Comment text cannot exceed 280 characters")
        tweet = (
            await db.execute(select(Tweet).where(Tweet.id == request.tweet_id))
        ).scalar_one_or_none()
        if not tweet:
            raise NotFoundError("Tweet not found")
        comment = Comment(
            tweet_id=request.tweet_id,
            user_id=user_id,
            text=request.text,
            parent_comment_id=request.parent_comment_id,
        )
        db.add(comment)
        try:
            await db.commit()
            await db.refresh(comment)
            # Optimized cache invalidation for comment
            await cache_service.invalidate_engagement_cache(request.tweet_id)
            await cache_service.invalidate_comment_cache(comment.id, request.tweet_id)
            await cache_service.invalidate_user_interaction_cache(user_id, "comment")
            await cache_service.invalidate_feed_for_followers(db, tweet.user_id)
            if request.parent_comment_id:
                await cache_service.invalidate_comment_cache(request.parent_comment_id)
            return await self.get_comment_response(db, comment.id, user_id)
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to comment on tweet: {e}")
            raise e

    async def edit_comment(
        self,
        db: AsyncSession,
        user_id: str,
        comment_id: int,
        text: str,
    ) -> CommentResponse:
        comment = (
            await db.execute(
                select(Comment).where(
                    Comment.id == comment_id, Comment.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        if not comment:
            raise NotFoundError("Comment not found or not owned by user")
        if not text or not text.strip():
            raise ValidationError("Comment text cannot be empty")
        if len(text) > 280:
            raise ValidationError("Comment text cannot exceed 280 characters")
        if comment.text == text:
            raise ValidationError("No changes provided for comment edit.")
        comment.text = text
        comment.edited_at = datetime.utcnow()
        try:
            await db.commit()
            await db.refresh(comment)
            await cache_service.invalidate_feed_for_followers(db, comment.user_id)
            await cache_service.invalidate_engagement_cache(comment.tweet_id)
            return await self.get_comment_response(db, comment.id, user_id)
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to edit comment: {e}")
            raise e

    async def like_comment(
        self, db: AsyncSession, user_id: str, request: LikeCommentRequest
    ) -> ActionResponse:
        await self._check_and_auto_unblock_user(db, user_id)
        comment = (
            await db.execute(select(Comment).where(Comment.id == request.comment_id))
        ).scalar_one_or_none()
        if not comment:
            raise NotFoundError("Comment not found")
        like = (
            await db.execute(
                select(CommentLike).where(
                    CommentLike.comment_id == request.comment_id,
                    CommentLike.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        try:
            if request.like:
                if not like:
                    db.add(CommentLike(comment_id=request.comment_id, user_id=user_id))
                    await db.commit()
                    # Optimized cache invalidation for comment like
                    await cache_service.invalidate_comment_cache(request.comment_id, comment.tweet_id)
                    await cache_service.invalidate_engagement_cache(comment.tweet_id)
                    await cache_service.invalidate_feed_for_followers(db, comment.user_id)
                return ActionResponse(success=True, message="Comment liked")
            else:
                if like:
                    await db.delete(like)
                    await db.commit()
                    # Optimized cache invalidation for comment unlike
                    await cache_service.invalidate_comment_cache(request.comment_id, comment.tweet_id)
                    await cache_service.invalidate_engagement_cache(comment.tweet_id)
                    await cache_service.invalidate_feed_for_followers(db, comment.user_id)
                return ActionResponse(success=True, message="Comment unliked")
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to like/unlike comment: {e}")
            raise e

    async def report_comment(
        self, db: AsyncSession, user_id: str, request: ReportCommentRequest
    ) -> ActionResponse:
        await self._check_and_auto_unblock_user(db, user_id)
        comment = (
            await db.execute(select(Comment).where(Comment.id == request.comment_id))
        ).scalar_one_or_none()
        if not comment:
            raise NotFoundError("Comment not found")
        if comment.user_id == user_id:
            raise ValidationError("You cannot report your own comment.")
        try:
            snapshot = await self.create_comment_snapshot(db, comment.id, user_id)
            report = CommentReport(
                comment_id=request.comment_id,
                user_id=user_id,
                reason=request.reason,
                snapshot=snapshot,
            )
            db.add(report)
            await db.commit()
            await cache_service.invalidate_engagement_cache(request.comment_id)
            await cache_service.invalidate_user_activity_cache(user_id, "report")
            return ActionResponse(success=True, message="Comment reported")
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to report comment: {e}")
            raise e

    async def get_comments(
        self, db: AsyncSession, tweet_id: int, current_user_id: str, page: int = 1, page_size: int = None
    ) -> tuple[list[CommentResponse], int]:
        if page_size is None:
            page_size = settings.COMMENT_PAGE_SIZE
        cache_key = f"tweet_comments:{tweet_id}:p{page}:s{page_size}:u{current_user_id}"
        cached = await cache_service.get(cache_key)
        if cached:
            logger.info(
                json.dumps(
                    {"event": "cache_hit", "key": cache_key, "type": "tweet_comments"}
                )
            )
            return [CommentResponse(**c) for c in cached["comments"]], cached["total"]
        logger.info(
            json.dumps(
                {"event": "cache_miss", "key": cache_key, "type": "tweet_comments"}
            )
        )
 
        total_query = select(func.count()).where(
            and_(
                Comment.tweet_id == tweet_id,
                Comment.parent_comment_id.is_(None)
            )
        )
        total = (await db.execute(total_query)).scalar_one()
    
        comments_query = (
            select(Comment, UserProfile, User)
            .join(UserProfile, Comment.user_id == UserProfile.user_id)
            .join(User, User.user_id == Comment.user_id)
            .where(
                Comment.tweet_id == tweet_id,
                Comment.parent_comment_id.is_(None),
                ~User.is_blocked,
            )
        )
        comments_result = await db.execute(comments_query)
        all_comment_rows = comments_result.all()
        
        if not all_comment_rows:
            cache_data = {"comments": [], "total": 0}
            await cache_service.set(cache_key, cache_data, ttl=300)
            return [], 0
        
        # Get like counts for all comments
        comment_ids = [row[0].id for row in all_comment_rows]
        like_counts = {}
        user_likes = {}
        
        if comment_ids:
            likes_query = (
                select(
                    CommentLike.comment_id,
                    func.count(CommentLike.comment_id).label("like_count"),
                    func.max(
                        case((CommentLike.user_id == current_user_id, 1), else_=0)
                    ).label("user_liked"),
                )
                .where(CommentLike.comment_id.in_(comment_ids))
                .group_by(CommentLike.comment_id)
            )
            likes_result = await db.execute(likes_query)
            for comment_id, like_count, user_liked in likes_result:
                like_counts[comment_id] = like_count
                user_likes[comment_id] = bool(user_liked)
        
        # Check which comments have replies from the current user
        user_reply_parent_ids = set()
        if comment_ids:
            user_replies_query = (
                select(Comment.parent_comment_id)
                .where(
                    and_(
                        Comment.tweet_id == tweet_id,
                        Comment.user_id == current_user_id,
                        Comment.parent_comment_id.in_(comment_ids)
                    )
                )
                .distinct()
            )
            user_replies_result = await db.execute(user_replies_query)
            user_reply_parent_ids = {row[0] for row in user_replies_result.all()}
        
        # Categorize comments
        user_comments = []  # Comments by current user
        user_replied_comments = []  # Comments with replies from current user
        other_comments = []  # All other comments
        
        for comment, profile, user in all_comment_rows:
            comment_data = {
                'comment': comment,
                'profile': profile,
                'user': user,
                'like_count': like_counts.get(comment.id, 0),
                'is_liked': user_likes.get(comment.id, False)
            }
            
            if comment.user_id == current_user_id:
                user_comments.append(comment_data)
            elif comment.id in user_reply_parent_ids:
                user_replied_comments.append(comment_data)
            else:
                other_comments.append(comment_data)
        
        # Sort each category
        # User's own comments: most recent first
        user_comments.sort(key=lambda x: x['comment'].created_at, reverse=True)
        
        # Comments with user's replies: most recent first
        user_replied_comments.sort(key=lambda x: x['comment'].created_at, reverse=True)
        
        # Other comments: by engagement (likes) then by recency
        other_comments.sort(key=lambda x: (x['like_count'], x['comment'].created_at), reverse=True)
        
        # Combine all comments in priority order
        all_sorted_comments = user_comments + user_replied_comments + other_comments
        
        # Apply pagination
        offset = (page - 1) * page_size
        paginated_comments = all_sorted_comments[offset:offset + page_size]
        
        # Build response objects
        responses = []
        for comment_data in paginated_comments:
            comment = comment_data['comment']
            profile = comment_data['profile']
            user = comment_data['user']
            
            response = CommentResponse(
                id=comment.id,
                tweet_id=comment.tweet_id,
                user_id=comment.user_id,
                text=comment.text,
                parent_comment_id=comment.parent_comment_id,
                like_count=comment_data['like_count'],
                is_liked=comment_data['is_liked'],
                created_at=comment.created_at,
                edited_at=comment.edited_at,
                user_name=(
                    profile.name if profile else (user.name if user else "Unknown User")
                ),
                photo=(
                    profile.photo_path
                    if profile and profile.photo_path and profile.photo_content_type
                    else None
                ),
                is_organizational=profile.is_organizational if profile else False,
                is_prime=profile.is_prime if profile else False,
            )
            responses.append(response)
        
        # Cache the results
        cache_ttl = 900 if responses else 300
        cache_data = {"comments": [r.model_dump() for r in responses], "total": total}
        await cache_service.set(cache_key, cache_data, ttl=cache_ttl)
        
        return responses, total

    async def get_comment_response(
        self, db: AsyncSession, comment_id: int, current_user_id: str
    ) -> CommentResponse:
        comment = (
            await db.execute(select(Comment).where(Comment.id == comment_id))
        ).scalar_one_or_none()
        if not comment:
            raise NotFoundError("Comment not found")
        user_profile = (
            await db.execute(
                select(UserProfile).where(UserProfile.user_id == comment.user_id)
            )
        ).scalar_one_or_none()
        user = (
            await db.execute(select(User).where(User.user_id == comment.user_id))
        ).scalar_one_or_none()
        like_count = len(
            (
                await db.execute(
                    select(CommentLike).where(CommentLike.comment_id == comment_id)
                )
            )
            .scalars()
            .all()
        )
        is_liked = (
            await db.execute(
                select(CommentLike).where(
                    CommentLike.comment_id == comment_id,
                    CommentLike.user_id == current_user_id,
                )
            )
        ).scalar_one_or_none() is not None
        return CommentResponse(
            id=comment.id,
            tweet_id=comment.tweet_id,
            user_id=comment.user_id,
            text=comment.text,
            parent_comment_id=comment.parent_comment_id,
            like_count=like_count,
            is_liked=is_liked,
            created_at=comment.created_at,
            edited_at=comment.edited_at,
            user_name=(
                user_profile.name
                if user_profile
                else (user.name if user else "Unknown User")
            ),
            photo=(
                user_profile.photo_path
                if user_profile
                and user_profile.photo_path
                and user_profile.photo_content_type
                else None
            ),
            is_organizational=user_profile.is_organizational if user_profile else False,
            is_prime=user_profile.is_prime if user_profile else False,
        )

    async def get_user_tweets(
        self,
        db: AsyncSession,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        requester_id: str = None,
    ) -> TweetFeedResponse:
        if not requester_id:
            raise ValidationError("Requester ID is required to check permissions.")
        profile = await user_profile_service.get_user_profile(db, user_id, requester_id)
        if (
            profile.is_organizational
            or not profile.is_private
            or profile.can_view_content
        ):
            offset = (page - 1) * page_size
            query = (
                select(Tweet)
                .where(Tweet.user_id == user_id)
                .order_by(Tweet.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            result = await db.execute(query)
            tweets = result.scalars().all()
            tweet_responses = []
            for tweet in tweets:
                tweet_response = await self.get_tweet_response(
                    db, tweet.id, requester_id
                )
                tweet_responses.append(tweet_response)
            total_query = select(func.count()).where(Tweet.user_id == user_id)
            total = (await db.execute(total_query)).scalar_one()
            return TweetFeedResponse(
                tweets=tweet_responses, total=total, page=page, page_size=page_size
            )
        raise ValidationError("You are not allowed to view this user's tweets.")

    async def get_my_tweets(
        self, db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
    ) -> TweetFeedResponse:
        offset = (page - 1) * page_size
        query = (
            select(Tweet)
            .where(Tweet.user_id == user_id)
            .order_by(Tweet.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(query)
        tweets = result.scalars().all()
        tweet_responses = []
        for tweet in tweets:
            tweet_response = await self.get_tweet_response(db, tweet.id, user_id)
            tweet_responses.append(tweet_response)
        total_query = select(func.count()).where(Tweet.user_id == user_id)
        total = (await db.execute(total_query)).scalar_one()
        return TweetFeedResponse(
            tweets=tweet_responses, total=total, page=page, page_size=page_size
        )

    async def get_liked_tweets(
        self, db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
    ) -> TweetFeedResponse:
        offset = (page - 1) * page_size
        liked_tweet_ids_query = (
            select(TweetLike.tweet_id)
            .where(TweetLike.user_id == user_id)
            .order_by(TweetLike.tweet_id.desc())
            .offset(offset)
            .limit(page_size)
        )
        liked_tweet_ids = (await db.execute(liked_tweet_ids_query)).scalars().all()
        tweets = []
        for tweet_id in liked_tweet_ids:
            tweet = await self.get_tweet_response(db, tweet_id, user_id)
            tweets.append(tweet)
        total_query = select(func.count()).where(TweetLike.user_id == user_id)
        total = (await db.execute(total_query)).scalar_one()
        return TweetFeedResponse(
            tweets=tweets, total=total, page=page, page_size=page_size
        )

    async def get_bookmarked_tweets(
        self, db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
    ) -> TweetFeedResponse:
        offset = (page - 1) * page_size
        bookmarked_tweet_ids_query = (
            select(Bookmark.tweet_id)
            .where(Bookmark.user_id == user_id)
            .order_by(Bookmark.tweet_id.desc())
            .offset(offset)
            .limit(page_size)
        )
        bookmarked_tweet_ids = (
            (await db.execute(bookmarked_tweet_ids_query)).scalars().all()
        )
        tweets = []
        for tweet_id in bookmarked_tweet_ids:
            tweet = await self.get_tweet_response(db, tweet_id, user_id)
            tweets.append(tweet)
        total_query = select(func.count()).where(Bookmark.user_id == user_id)
        total = (await db.execute(total_query)).scalar_one()
        return TweetFeedResponse(
            tweets=tweets, total=total, page=page, page_size=page_size
        )

    async def get_my_comments(
        self, db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
    ) -> list:
        offset = (page - 1) * page_size
        comments_query = (
            select(Comment)
            .where(Comment.user_id == user_id)
            .order_by(Comment.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        comments = (await db.execute(comments_query)).scalars().all()
        responses = []
        for comment in comments:
            response = await self.get_comment_response(db, comment.id, user_id)
            tweet = (await db.execute(select(Tweet).where(Tweet.id == comment.tweet_id))).scalar_one_or_none()
            tweet_author = None
            if tweet:
                author_profile = (
                    await db.execute(select(UserProfile).where(UserProfile.user_id == tweet.user_id))
                ).scalar_one_or_none()
                tweet_author = {
                    "user_id": tweet.user_id,
                    "name": author_profile.name if author_profile else None,
                    "photo": author_profile.photo_path if author_profile else None,
                    "is_organizational": author_profile.is_organizational if author_profile else False,
                    "is_prime": author_profile.is_prime if author_profile else False,
                }
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response.dict()
            response_dict["tweet_author"] = tweet_author
            responses.append(response_dict)
        return responses

    async def get_sent_shared_tweets(
        self, db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
    ) -> list:
        """Get tweets shared by the current user"""
        
        cache_key = f"sent_shared_tweets:{user_id}:p{page}:s{page_size}"
        cached = await cache_service.get(cache_key)
        if cached:
            logger.info(f"Cache hit for sent shared tweets: {cache_key}")
            return [SharedTweetResponse(**item) for item in cached]

        offset = (page - 1) * page_size
        shares_query = (
            select(Share)
            .where(Share.user_id == user_id)
            .order_by(desc(Share.shared_at))
            .offset(offset)
            .limit(page_size)
        )
        shares = (await db.execute(shares_query)).scalars().all()
        result = []
        
        for share in shares:
            # Get tweet details
            tweet_response = await self.get_tweet_response(db, share.tweet_id, user_id)
            
            # Get sender profile
            sender_profile = (
                await db.execute(
                    select(UserProfile).where(UserProfile.user_id == share.user_id)
                )
            ).scalar_one_or_none()
            
            # Get recipient profile
            recipient_profile = (
                await db.execute(
                    select(UserProfile).where(UserProfile.user_id == share.recipient_id)
                )
            ).scalar_one_or_none()
            
            # Count images in the tweet
            media_query = (
                await db.execute(
                    select(func.count(TweetMedia.id))
                    .where(TweetMedia.tweet_id == share.tweet_id)
                )
            )
            image_count = media_query.scalar_one() or 0
            
            shared_tweet = SharedTweetResponse(
                id=share.id,
                tweet_id=share.tweet_id,
                sender_id=share.user_id,
                sender_name=sender_profile.name if sender_profile else "Unknown",
                sender_photo_path=sender_profile.photo_path if sender_profile else None,
                recipient_id=share.recipient_id,
                recipient_name=recipient_profile.name if recipient_profile else "Unknown",
                recipient_photo_path=recipient_profile.photo_path if recipient_profile else None,
                message=share.message,
                shared_at=share.shared_at,
                tweet=tweet_response,
                image_count=image_count
            )
            result.append(shared_tweet)
        
        # Cache the result
        await cache_service.set(cache_key, [item.dict() for item in result], ttl=300)
        return result

    async def get_received_shared_tweets(
        self, db: AsyncSession, user_id: str, page: int = 1, page_size: int = 20
    ) -> list:
        """Get tweets shared to the current user"""
        
        cache_key = f"received_shared_tweets:{user_id}:p{page}:s{page_size}"
        cached = await cache_service.get(cache_key)
        if cached:
            logger.info(f"Cache hit for received shared tweets: {cache_key}")
            return [SharedTweetResponse(**item) for item in cached]

        offset = (page - 1) * page_size
        shares_query = (
            select(Share)
            .where(Share.recipient_id == user_id)
            .order_by(desc(Share.shared_at))
            .offset(offset)
            .limit(page_size)
        )
        shares = (await db.execute(shares_query)).scalars().all()
        result = []
        
        for share in shares:
            # Get tweet details
            tweet_response = await self.get_tweet_response(db, share.tweet_id, user_id)
            
            # Get sender profile
            sender_profile = (
                await db.execute(
                    select(UserProfile).where(UserProfile.user_id == share.user_id)
                )
            ).scalar_one_or_none()
            
            # Get recipient profile
            recipient_profile = (
                await db.execute(
                    select(UserProfile).where(UserProfile.user_id == share.recipient_id)
                )
            ).scalar_one_or_none()
            
            # Count images in the tweet
            media_query = (
                await db.execute(
                    select(func.count(TweetMedia.id))
                    .where(TweetMedia.tweet_id == share.tweet_id)
                )
            )
            image_count = media_query.scalar_one() or 0
            
            shared_tweet = SharedTweetResponse(
                id=share.id,
                tweet_id=share.tweet_id,
                sender_id=share.user_id,
                sender_name=sender_profile.name if sender_profile else "Unknown",
                sender_photo_path=sender_profile.photo_path if sender_profile else None,
                recipient_id=share.recipient_id,
                recipient_name=recipient_profile.name if recipient_profile else "Unknown",
                recipient_photo_path=recipient_profile.photo_path if recipient_profile else None,
                message=share.message,
                shared_at=share.shared_at,
                tweet=tweet_response,
                image_count=image_count
            )
            result.append(shared_tweet)
        
        # Cache the result
        await cache_service.set(cache_key, [item.dict() for item in result], ttl=300)
        return result

    async def get_all_comments_flat(self, db: AsyncSession, tweet_id: int, user_id: str) -> list[CommentResponse]:
        comments_query = (
            select(Comment)
            .where(Comment.tweet_id == tweet_id)
            .order_by(Comment.created_at.asc())
        )
        comments = (await db.execute(comments_query)).scalars().all()
        responses = []
        for comment in comments:
            response = await self.get_comment_response(db, comment.id, user_id)
            responses.append(response)
        return responses

    async def delete_comment(self, db: AsyncSession, user_id: str, comment_id: int) -> ActionResponse:
        comment = (
            await db.execute(
                select(Comment).where(Comment.id == comment_id, Comment.user_id == user_id)
            )
        ).scalar_one_or_none()
        if not comment:
            raise NotFoundError("Comment not found or not owned by user")
        await db.execute(Comment.__table__.delete().where(Comment.parent_comment_id == comment_id))
        await db.delete(comment)
        try:
            await db.commit()
            await cache_service.invalidate_engagement_cache(comment.tweet_id)
            await cache_service.invalidate_feed_for_followers(db, comment.user_id)
            return ActionResponse(success=True, message="Comment deleted")
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to delete comment: {e}")
            raise e

    async def get_comment_replies(self, db: AsyncSession, comment_id: int, user_id: str, page: int = 1, page_size: int = 20) -> list[CommentResponse]:
        offset = (page - 1) * page_size
        replies_query = (
            select(Comment)
            .where(Comment.parent_comment_id == comment_id)
            .order_by(Comment.created_at.asc())
            .offset(offset)
            .limit(page_size)
        )
        replies = (await db.execute(replies_query)).scalars().all()
        responses = []
        for reply in replies:
            response = await self.get_comment_response(db, reply.id, user_id)
            responses.append(response)
        return responses

    async def delete_tweet(self, db: AsyncSession, user_id: str, tweet_id: int) -> ActionResponse:
        tweet = (
            await db.execute(
                select(Tweet).where(Tweet.id == tweet_id, Tweet.user_id == user_id)
            )
        ).scalar_one_or_none()
        if not tweet:
            raise NotFoundError("Tweet not found or not owned by user")
        await db.execute(TweetMedia.__table__.delete().where(TweetMedia.tweet_id == tweet_id))
        await db.execute(TweetLike.__table__.delete().where(TweetLike.tweet_id == tweet_id))
        await db.execute(Bookmark.__table__.delete().where(Bookmark.tweet_id == tweet_id))
        await db.execute(Share.__table__.delete().where(Share.tweet_id == tweet_id))
        comment_ids = (await db.execute(select(Comment.id).where(Comment.tweet_id == tweet_id))).scalars().all()
        if comment_ids:
            await db.execute(CommentLike.__table__.delete().where(CommentLike.comment_id.in_(comment_ids)))
            await db.execute(CommentReport.__table__.delete().where(CommentReport.comment_id.in_(comment_ids)))
            await db.execute(Comment.__table__.delete().where(Comment.id.in_(comment_ids)))
        await db.execute(TweetReport.__table__.delete().where(TweetReport.tweet_id == tweet_id))
        await db.delete(tweet)
        try:
            await db.commit()
            await cache_service.invalidate_feed_for_followers(db, user_id)
            await cache_service.invalidate_user_cache(user_id)
            await cache_service.invalidate_twitter_recommendation_cache()
            await cache_service.invalidate_engagement_cache(tweet_id)
            return ActionResponse(success=True, message="Tweet deleted")
        except BaseCustomException as e:
            await db.rollback()
            logger.error(f"Failed to delete tweet: {e}")
            raise e

    async def get_mutual_followers_for_user(
        self, db: AsyncSession, user_id: str, candidate_user_ids: list[str] = None
    ) -> list[str]:
        """Get mutual followers between user and candidate users."""
        if candidate_user_ids:
            sorted_candidates = sorted(candidate_user_ids)
            cache_key = f"mutual_followers:{user_id}:candidates:{'-'.join(sorted_candidates)}"
        else:
            cache_key = f"mutual_followers:{user_id}:all"
        cached = await cache_service.get(cache_key)
        if cached:
            logger.info(f"Cache hit for mutual followers: {cache_key}")
            return cached
        if not candidate_user_ids:
            # Get all mutual followers if no specific candidates provided
            following_query = select(Follower.followee_id).where(
                Follower.follower_id == user_id
            )
            following_result = await db.execute(following_query)
            following_ids = [row[0] for row in following_result.all()]

            if not following_ids:
                return []

            followers_query = select(Follower.follower_id).where(
                and_(
                    Follower.followee_id == user_id,
                    Follower.follower_id.in_(following_ids),
                )
            )
            followers_result = await db.execute(followers_query)
            mutual_followers = [row[0] for row in followers_result.all()]
            
            # Cache the result
            await cache_service.set(cache_key, mutual_followers, ttl=300)  # 5 minutes TTL
            return mutual_followers
        else:
            # Check mutual relationship with specific candidates
            following_query = select(Follower.followee_id).where(
                and_(
                    Follower.follower_id == user_id,
                    Follower.followee_id.in_(candidate_user_ids),
                )
            )
            following_result = await db.execute(following_query)
            following_ids = {row[0] for row in following_result.all()}
            
            followers_query = select(Follower.follower_id).where(
                and_(
                    Follower.followee_id == user_id,
                    Follower.follower_id.in_(candidate_user_ids),
                )
            )
            followers_result = await db.execute(followers_query)
            followers_ids = {row[0] for row in followers_result.all()}

            # Return users who both follow and are followed by current user
            mutual_followers = list(following_ids & followers_ids)
            
            # Cache the result
            await cache_service.set(cache_key, mutual_followers, ttl=300)  # 5 minutes TTL
            return mutual_followers


tweet_service = TweetCruds()
