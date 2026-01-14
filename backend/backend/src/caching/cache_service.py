import redis.asyncio as redis
from typing import Optional, List, Any
from core.config import get_settings
from core.exceptions import InternalServerError
import json
import logging
import gzip
import time
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from user_profile.models.Follower import Follower
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)
settings = get_settings()
CACHE_VERSION = "v2"

# Cache monitoring metrics
class CacheMetrics:
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.operations = defaultdict(int)
        self.compression_savings = 0
        self.last_reset = time.time()
        
    def record_hit(self):
        self.hits += 1
        
    def record_miss(self):
        self.misses += 1
        
    def record_error(self):
        self.errors += 1
        
    def record_operation(self, operation: str):
        self.operations[operation] += 1
        
    def record_compression_savings(self, original_size: int, compressed_size: int):
        self.compression_savings += (original_size - compressed_size)
        
    def get_hit_ratio(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0
        
    def reset(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.operations.clear()
        self.compression_savings = 0
        self.last_reset = time.time()
        
    def get_stats(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_ratio": self.get_hit_ratio(),
            "operations": dict(self.operations),
            "compression_savings_bytes": self.compression_savings,
            "uptime_seconds": time.time() - self.last_reset
        }

# Global metrics instance
cache_metrics = CacheMetrics()

def versioned_key(key: str) -> str:
    return f"{CACHE_VERSION}:{key}"

def should_compress(data: str, threshold: int = 1024) -> bool:
    """Determine if data should be compressed based on size"""
    return len(data.encode('utf-8')) > threshold

def compress_data(data: str) -> bytes:
    """Compress string data using gzip"""
    return gzip.compress(data.encode('utf-8'))

def decompress_data(data: bytes) -> str:
    """Decompress gzip data back to string"""
    return gzip.decompress(data).decode('utf-8')

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class CacheService:
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._connected = False
        self._connection_pool: Optional[redis.ConnectionPool] = None
        self.compression_enabled = True
        self.compression_threshold = 1024  # bytes

    async def connect(self) -> None:
        if self._connected:
            return
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=100,
                retry_on_timeout=True,
                retry_on_error=[redis.BusyLoadingError, redis.ConnectionError],
                socket_timeout=5,
                socket_connect_timeout=5,
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30,
                decode_responses=False,  # Changed to False to handle binary data
                encoding="utf-8",
                db=0,
                protocol=3,
            )
            self._redis = redis.Redis(
                connection_pool=self._connection_pool,
                socket_timeout=5,
                retry_on_timeout=True,
                retry_on_error=[redis.BusyLoadingError, redis.ConnectionError],
                health_check_interval=30,
            )
            await self._redis.ping()
            self._connected = True
            logger.info("Connected to Redis with optimized pool")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise InternalServerError(f"Cache service unavailable: {e}")

    async def disconnect(self) -> None:
        if self._redis and self._connected:
            await self._redis.close()
            if self._connection_pool:
                await self._connection_pool.disconnect()
            self._connected = False
            logger.info("Redis connection closed")

    @asynccontextmanager
    async def _redis_operation(self, operation_name: str):
        max_retries = 3
        retry_delay = 0.1
        for attempt in range(max_retries):
            try:
                if not self._connected:
                    await self.connect()
                yield
                return
            except (redis.ConnectionError, redis.TimeoutError) as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Redis {operation_name} attempt {attempt + 1} failed, retrying: {e}"
                    )
                    await asyncio.sleep(retry_delay * (2**attempt))
                else:
                    logger.error(
                        f"Redis {operation_name} failed after {max_retries} attempts: {e}"
                    )
                    raise
            except Exception as e:
                logger.error(f"Redis {operation_name} error: {e}")
                raise

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, compress: Optional[bool] = None) -> bool:
        try:
            async with self._redis_operation("set"):
                cache_metrics.record_operation("set")
                
                original_key = key
                key = versioned_key(key)
                
                # Serialize the value
                if isinstance(value, (dict, list)):
                    serialized_value = json.dumps(
                        value, separators=(",", ":"), cls=DateTimeEncoder
                    )
                elif isinstance(value, str):
                    serialized_value = value
                else:
                    serialized_value = json.dumps(
                        value, separators=(",", ":"), cls=DateTimeEncoder
                    )
                
                # Determine if compression should be used
                use_compression = compress if compress is not None else (
                    self.compression_enabled and should_compress(serialized_value, self.compression_threshold)
                )
                
                store_value = serialized_value
                compression_flag = "0"  # 0 = not compressed, 1 = compressed
                
                if use_compression:
                    try:
                        original_size = len(serialized_value.encode('utf-8'))
                        compressed_data = compress_data(serialized_value)
                        compressed_size = len(compressed_data)
                        
                        # Only use compression if it actually saves space
                        if compressed_size < original_size * 0.9:  # At least 10% savings
                            store_value = compressed_data
                            compression_flag = "1"
                            cache_metrics.record_compression_savings(original_size, compressed_size)
                            logger.debug(f"Compressed cache data for key {original_key}: {original_size} -> {compressed_size} bytes")
                    except Exception as e:
                        logger.warning(f"Compression failed for key {original_key}, storing uncompressed: {e}")
                
                # Store with compression flag prefix
                final_value = f"{compression_flag}:{store_value}" if isinstance(store_value, str) else store_value
                
                pipe = self._redis.pipeline()
                if ttl:
                    if isinstance(final_value, bytes):
                        # For compressed data, we need to handle bytes differently
                        # Prepend compression flag to compressed bytes
                        final_bytes = b"1:" + final_value
                        await self._redis.setex(key, ttl, final_bytes)
                    else:
                        # Encode string to bytes before storing
                        pipe.setex(key, ttl, final_value.encode('utf-8'))
                else:
                    if isinstance(final_value, bytes):
                        # Prepend compression flag to compressed bytes
                        final_bytes = b"1:" + final_value
                        await self._redis.set(key, final_bytes)
                    else:
                        # Encode string to bytes before storing
                        pipe.set(key, final_value.encode('utf-8'))
                
                if not isinstance(final_value, bytes):
                    results = await pipe.execute()
                    return bool(results[0])
                return True
                
        except Exception as e:
            cache_metrics.record_error()
            logger.error(f"Cache set error for key {original_key}: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        try:
            async with self._redis_operation("get"):
                cache_metrics.record_operation("get")
                
                original_key = key
                key = versioned_key(key)
                value = await self._redis.get(key)
                
                if value is None:
                    cache_metrics.record_miss()
                    return None
                
                cache_metrics.record_hit()
                
                # Handle compressed data
                if isinstance(value, bytes):
                    # Check for compression flag in binary data
                    if value.startswith(b"1:"):
                        # This is compressed data
                        try:
                            compressed_data = value[2:]  # Skip the "1:" prefix
                            decompressed_value = decompress_data(compressed_data)
                            return json.loads(decompressed_value)
                        except Exception as e:
                            logger.warning(f"Failed to decompress cache data for key {original_key}: {e}")
                            return None
                    else:
                        # Try to decode as UTF-8 string
                        try:
                            decoded_value = value.decode('utf-8')
                            if decoded_value.startswith(("0:", "1:")):
                                # Check for compression flag
                                compression_flag, actual_value = decoded_value.split(":", 1)
                                if compression_flag == "1":
                                    # This should not happen as compressed data should be bytes
                                    logger.warning(f"Unexpected compressed string data for key {original_key}")
                                    return None
                                else:
                                    # Uncompressed data
                                    try:
                                        return json.loads(actual_value)
                                    except json.JSONDecodeError:
                                        return actual_value
                            else:
                                # Legacy data without compression flag
                                try:
                                    return json.loads(decoded_value)
                                except json.JSONDecodeError:
                                    return decoded_value
                        except UnicodeDecodeError:
                            logger.error(f"Failed to decode cache data for key {original_key}")
                            return None
                else:
                    # This shouldn't happen with decode_responses=False
                    logger.warning(f"Unexpected string value from Redis for key {original_key}")
                    return None
                        
        except Exception as e:
            cache_metrics.record_error()
            logger.error(f"Cache get error for key {original_key}: {e}")
            return None

    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        try:
            async with self._redis_operation("mget"):
                versioned_keys = [versioned_key(k) for k in keys]
                values = await self._redis.mget(versioned_keys)
                results = []
                for value in values:
                    if value is None:
                        results.append(None)
                    else:
                        # Handle binary data
                        if isinstance(value, bytes):
                            try:
                                decoded_value = value.decode('utf-8')
                                if decoded_value.startswith(("0:", "1:")):
                                    compression_flag, actual_value = decoded_value.split(":", 1)
                                    if compression_flag == "0":
                                        try:
                                            results.append(json.loads(actual_value))
                                        except json.JSONDecodeError:
                                            results.append(actual_value)
                                    else:
                                        # Should not happen - compressed data should use binary prefix
                                        results.append(None)
                                else:
                                    try:
                                        results.append(json.loads(decoded_value))
                                    except json.JSONDecodeError:
                                        results.append(decoded_value)
                            except UnicodeDecodeError:
                                # Try as compressed data
                                if value.startswith(b"1:"):
                                    try:
                                        compressed_data = value[2:]
                                        decompressed_value = decompress_data(compressed_data)
                                        results.append(json.loads(decompressed_value))
                                    except Exception:
                                        results.append(None)
                                else:
                                    results.append(None)
                        else:
                            results.append(None)
                return results
        except Exception as e:
            logger.error(f"Cache mget error for keys {keys}: {e}")
            return [None] * len(keys)

    async def mset(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        try:
            async with self._redis_operation("mset"):
                versioned_mapping = {}
                for key, value in mapping.items():
                    versioned_key_name = versioned_key(key)
                    if isinstance(value, (dict, list)):
                        serialized_value = json.dumps(
                            value, separators=(",", ":"), cls=DateTimeEncoder
                        )
                    elif isinstance(value, str):
                        serialized_value = value
                    else:
                        serialized_value = json.dumps(
                            value, separators=(",", ":"), cls=DateTimeEncoder
                        )
                    # Encode to bytes with compression flag
                    versioned_mapping[versioned_key_name] = f"0:{serialized_value}".encode('utf-8')
                pipe = self._redis.pipeline()
                pipe.mset(versioned_mapping)
                if ttl:
                    for key in versioned_mapping.keys():
                        pipe.expire(key, ttl)
                results = await pipe.execute()
                return bool(results[0])
        except Exception as e:
            logger.error(f"Cache mset error: {e}")
            return False

    async def delete(self, *keys: str) -> int:
        try:
            async with self._redis_operation("delete"):
                versioned_keys = [versioned_key(k) for k in keys if k]
                if not versioned_keys:
                    return 0
                if len(versioned_keys) > 100:
                    total_deleted = 0
                    for i in range(0, len(versioned_keys), 100):
                        chunk = versioned_keys[i : i + 100]
                        deleted = await self._redis.delete(*chunk)
                        total_deleted += deleted
                    return total_deleted
                else:
                    return await self._redis.delete(*versioned_keys)
        except Exception as e:
            logger.error(f"Cache delete error for keys {keys}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        try:
            async with self._redis_operation("exists"):
                key = versioned_key(key)
                return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def keys(self, pattern: str) -> List[str]:
        try:
            async with self._redis_operation("keys"):
                pattern = versioned_key(pattern)
                return await self._redis.keys(pattern)
        except Exception as e:
            logger.error(f"Cache keys error for pattern {pattern}: {e}")
            return []

    async def delete_pattern(self, pattern: str) -> int:
        try:
            async with self._redis_operation("delete_pattern"):
                if not pattern.startswith(CACHE_VERSION):
                    pattern = versioned_key(pattern)
                deleted_count = 0
                cursor = 0
                while True:
                    cursor, items = await self._redis.scan(
                        cursor, match=pattern, count=100
                    )
                    if items:
                        deleted = await self._redis.delete(*items)
                        deleted_count += deleted
                    if cursor == 0:
                        break
                await self.warn_if_many_deleted(pattern, deleted_count)
                return deleted_count
        except Exception as e:
            logger.error(f"Cache delete_pattern error for pattern {pattern}: {e}")
            return 0

    async def get_cache_stats(self) -> dict:
        try:
            async with self._redis_operation("get_cache_stats"):
                info = await self._redis.info()
                return {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "0B"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "hit_rate": (
                        info.get("keyspace_hits", 0)
                        / max(
                            info.get("keyspace_hits", 0)
                            + info.get("keyspace_misses", 0),
                            1,
                        )
                    )
                    * 100,
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "instantaneous_ops_per_sec": info.get(
                        "instantaneous_ops_per_sec", 0
                    ),
                }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

    async def invalidate_admin_cache(self) -> None:
        try:
            patterns = [
                "admin:all_users:*",
                "admin:blocked_users:*",
                "admin:user_stats:*",
                "admin:tweet_stats:*",
                "admin_search_users:*",
                "admin_user_type_stats*",
                "admin_user_activity_stats*",
                "admin_tweet_reports:*",
            ]
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_deleted = sum(r for r in results if isinstance(r, int))
            logger.info(f"Invalidated admin caches: {total_deleted} keys deleted")
        except Exception as e:
            logger.error(f"Failed to invalidate admin caches: {e}")

    async def invalidate_user_admin_cache(self, user_id: str) -> None:
        try:
            patterns = [
                f"admin:user:{user_id}:*",
                f"admin:user_stats:{user_id}:*",
                f"admin:tweet_stats:{user_id}:*",
            ]
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            await asyncio.gather(*tasks, return_exceptions=True)
            await self.invalidate_admin_cache()
        except Exception as e:
            logger.error(f"Failed to invalidate admin caches for user {user_id}: {e}")

    async def invalidate_user_cache(self, user_id: str) -> None:
        try:
            patterns = [
                f"user:{user_id}:*",
                f"user:{user_id}",
                f"profile:{user_id}:*",
                f"profile:{user_id}",
                f"token:{user_id}:*",
                f"token:{user_id}",
                f"tweet:{user_id}:*",
                f"tweet:{user_id}",
                f"tweet_feed:{user_id}:*",
                f"tweet_feed:{user_id}",
                f"recommendations:{user_id}:*",
                f"recommendations:{user_id}",
                f"twitter_feed:{user_id}:*",
                f"twitter_feed:{user_id}",
                f"following_eggs:{user_id}:*",
                f"following_eggs:{user_id}",
                f"user_flags:{user_id}:*",
                f"user_flags:{user_id}",
                "user_search:*",
            ]
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_deleted = sum(r for r in results if isinstance(r, int))
            await self.invalidate_user_admin_cache(user_id)
            logger.info(
                f"Invalidated all caches for user {user_id}: {total_deleted} keys"
            )
        except Exception as e:
            logger.error(f"Failed to invalidate caches for user {user_id}: {e}")

    async def invalidate_user_tokens(self, user_id: str) -> None:
        try:
            patterns = [f"access_token:{user_id}:*", f"refresh_token:{user_id}:*"]
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Failed to invalidate tokens for user {user_id}: {e}")

    async def invalidate_profile_cache(self, user_id: str) -> None:
        try:
            patterns = [
                f"profile:{user_id}:*",
                f"profile:{user_id}",
                f"profile:{user_id}:req:*",
                "user_search:*",
            ]
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Invalidated profile cache for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to invalidate profile cache for user {user_id}: {e}")

    async def invalidate_interests_cache(self, user_id: str) -> None:
        try:
            patterns = [f"interests:{user_id}:*", f"user_interests:{user_id}:*"]
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Invalidated interests cache for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to invalidate interests cache: {e}")

    async def invalidate_follow_cache(
        self, follower_id: str = None, followee_id: str = None
    ) -> None:
        """Invalidate follow-related caches."""
        patterns = []
        if follower_id:
            patterns.extend([
                f"followers:{follower_id}:*",
                f"following:{follower_id}:*",
                f"follow_requests:{follower_id}:*",
                f"mutual_followers:{follower_id}:*",  # Add mutual followers invalidation
            ])
        if followee_id:
            patterns.extend([
                f"followers:{followee_id}:*",
                f"following:{followee_id}:*",
                f"follow_requests:{followee_id}:*", 
                f"mutual_followers:{followee_id}:*",  # Add mutual followers invalidation
            ])
        if not follower_id and not followee_id:
            patterns.extend(["followers:*", "following:*", "follow_requests:*", "mutual_followers:*"])
        
        try:
            deleted = 0
            for pattern in patterns:
                result = await self.delete_pattern(pattern)
                deleted += result
            logger.info(f"Invalidated {deleted} follow-related cache items")
        except Exception as e:
            logger.error(f"Failed to invalidate follow cache: {e}")
            raise InternalServerError(f"Failed to invalidate follow cache: {e}")

    async def invalidate_tweet_feed_cache(self, user_id: str):
        try:
            patterns = [
                f"tweet_feed:{user_id}:*",
                f"tweet_feed:{user_id}",
                f"twitter_feed:{user_id}:*",
                f"merged_feed:{user_id}:*",
                f"user_tweets:{user_id}:*",
                f"liked_tweets:{user_id}:*",
                f"bookmarked_tweets:{user_id}:*",
                f"shared_tweets:{user_id}:*",
                f"twitter_feed:{user_id}",
                f"recommendations:{user_id}:*",
                f"recommendations:{user_id}",
                f"twitter_feed:{user_id}:p*:*",
                f"engagement_batch:{user_id}:*",  # User-specific engagement cache
                f"user_flags:{user_id}:*",
                f"following_optimized:{user_id}:*",
                f"engagement_velocity:{user_id}:*",  # User-specific velocity cache
                f"media_batch:{user_id}:*",  # User-specific media cache
            ]
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Invalidated tweet feed cache for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to invalidate tweet feed cache: {e}")

    async def invalidate_feed_for_followers(self, db: AsyncSession, user_id: str):
        try:
            followers_cache_key = f"followers:user:{user_id}"
            follower_ids = await self.get(followers_cache_key)
            if not follower_ids:
                followers_result = await db.execute(
                    select(Follower.follower_id)
                    .where(Follower.followee_id == user_id)
                    .limit(10000)
                )
                follower_ids = [row[0] for row in followers_result.all()]
                await self.set(followers_cache_key, follower_ids, ttl=300)
            if follower_ids:
                chunk_size = 50
                tasks = []
                for i in range(0, len(follower_ids), chunk_size):
                    chunk = follower_ids[i : i + chunk_size]
                    chunk_tasks = [
                        self.invalidate_tweet_feed_cache(fid) for fid in chunk
                    ]
                    tasks.extend(chunk_tasks)
                for i in range(0, len(tasks), 20):
                    batch = tasks[i : i + 20]
                    await asyncio.gather(*batch, return_exceptions=True)
                logger.info(
                    f"Invalidated feed cache for {len(follower_ids)} followers of user {user_id}"
                )
        except Exception as e:
            logger.error(
                f"Failed to invalidate feed cache for followers of user {user_id}: {e}"
            )

    async def invalidate_twitter_recommendation_cache(self):
        try:
            patterns = [
                "twitter_feed:*",
                "recommendation_global:*",
                "trending_tweets:*",
                "priority_users:*",
                "all_user_metadata:*",
                "engagement_batch:*",
                "engagement_velocity:*",
                "media_batch:*",
                "following_optimized:*",
            ]
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("Invalidated global Twitter recommendation caches")
        except Exception as e:
            logger.error(f"Failed to invalidate Twitter recommendation cache: {e}")

    async def invalidate_engagement_cache(self, tweet_id: int):
        try:
            patterns = [
                f"engagement_batch:*",  # Keep global pattern for broad invalidation
                f"engagement_velocity:*",
                f"tweet_response:{tweet_id}:*",
                f"tweet_likes:{tweet_id}:*",
                f"tweet_comments:{tweet_id}:*",
                f"tweet_bookmarks:{tweet_id}:*",
                f"tweet_shares:{tweet_id}:*",
                f"tweet_stats:{tweet_id}:*",
                f"comment_count:{tweet_id}:*",
                f"like_count:{tweet_id}:*",
            ]
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Invalidated engagement cache for tweet {tweet_id}")
        except Exception as e:
            logger.error(
                f"Failed to invalidate engagement cache for tweet {tweet_id}: {e}"
            )

    async def invalidate_merged_feed_cache(self, user_id: str):
        await self.invalidate_tweet_feed_cache(user_id)

    async def invalidate_user_recommendations_cache(self, user_id: str = None):
        try:
            if user_id:
                patterns = [
                    f"recommendations:{user_id}:*",
                    f"recommendations:{user_id}",
                ]
            else:
                patterns = ["recommendations:*", "recommended_users:*"]
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Failed to invalidate recommendations cache: {e}")

    async def invalidate_tweet_media_cache(self, tweet_ids: list = None):
        try:
            if tweet_ids:
                patterns = [
                    "media_batch:*",
                ]
            else:
                patterns = [
                    "tweet_media:*", 
                    "media_batch:*",
                ]
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Failed to invalidate tweet media cache: {e}")

    async def invalidate_follow_related_feeds(self, follower_id: str, followee_id: str):
        try:
            await asyncio.gather(
                self.invalidate_tweet_feed_cache(follower_id),
                self.invalidate_tweet_feed_cache(followee_id),
                self.invalidate_follow_cache(follower_id, followee_id),
                return_exceptions=True,
            )
        except Exception as e:
            logger.error(f"Failed to invalidate follow-related feeds: {e}")

    async def smart_cache_warm_up(self, user_id: str, db: AsyncSession = None):
        """Intelligent cache warming for frequently accessed user data"""
        try:
            # Critical cache keys for user experience
            cache_keys = [
                f"profile:{user_id}",
                f"following_eggs:{user_id}",
                f"user_metadata:{user_id}",
                f"followers:{user_id}:p1:s20",
                f"following:{user_id}:p1:s20",
                f"user_flags:{user_id}",
            ]
            
            existing = await self.mget(cache_keys)
            missing_keys = [
                key for key, value in zip(cache_keys, existing) if value is None
            ]
            
            if missing_keys:
                logger.info(
                    f"Warming up {len(missing_keys)} cache keys for user {user_id}: {missing_keys}"
                )
                
                # Pre-warm critical data if database session is available
                if db and len(missing_keys) > 2:
                    await self._preload_user_essentials(user_id, db)
                    
        except Exception as e:
            logger.error(f"Failed to warm up cache for user {user_id}: {e}")

    async def _preload_user_essentials(self, user_id: str, db: AsyncSession):
        """Preload essential user data to cache"""
        try:
            # This would typically trigger the CRUD methods that populate cache
            # but we'll just log for now to avoid circular imports
            logger.info(f"Preloading essential data for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to preload essentials for user {user_id}: {e}")

    async def bulk_cache_operations(self, operations: list[dict]):
        """Perform multiple cache operations efficiently"""
        try:
            set_operations = []
            delete_operations = []
            
            for op in operations:
                if op["type"] == "set":
                    set_operations.append((op["key"], op["value"], op.get("ttl")))
                elif op["type"] == "delete":
                    delete_operations.append(op["key"])
            
            # Batch set operations
            if set_operations:
                set_mapping = {}
                ttl_keys = []
                for key, value, ttl in set_operations:
                    set_mapping[key] = value
                    if ttl:
                        ttl_keys.append((key, ttl))
                
                await self.mset(set_mapping)
                
                # Apply TTLs
                for key, ttl in ttl_keys:
                    await self.set(key, set_mapping[key], ttl)
            
            # Batch delete operations
            if delete_operations:
                await self.delete(*delete_operations)
            
            logger.info(f"Completed bulk cache operations: {len(set_operations)} sets, {len(delete_operations)} deletes")
            
        except Exception as e:
            logger.error(f"Failed bulk cache operations: {e}")

    async def cache_with_lock(self, key: str, compute_func, ttl: int = 300, lock_ttl: int = 10):
        """Cache data with distributed lock to prevent cache stampede"""
        try:
            # Try to get from cache first
            cached_value = await self.get(key)
            if cached_value is not None:
                return cached_value
            
            # Acquire lock to compute value
            lock_acquired = await self.acquire_lock(f"compute:{key}", lock_ttl)
            if not lock_acquired:
                # Another process is computing, wait briefly and try cache again
                await asyncio.sleep(0.1)
                cached_value = await self.get(key)
                if cached_value is not None:
                    return cached_value
                # If still not available, compute anyway (fallback)
            
            try:
                # Compute the value
                computed_value = await compute_func()
                
                # Cache the result
                await self.set(key, computed_value, ttl)
                
                return computed_value
                
            finally:
                if lock_acquired:
                    await self.release_lock(f"compute:{key}")
                    
        except Exception as e:
            logger.error(f"Failed cache_with_lock for key {key}: {e}")
            # Fallback to direct computation
            return await compute_func()

    async def invalidate_user_activity_cache(
        self, user_id: str, activity_type: str = "all"
    ):
        try:
            patterns = [
                f"user_flags:{user_id}:*",
                f"user_activity:{user_id}:*",
                f"engagement_batch:{user_id}:*",  # User-specific engagement cache
                f"engagement_velocity:{user_id}:*",  # User-specific velocity cache
                f"media_batch:{user_id}:*",  # User-specific media cache
            ]
            if activity_type == "like":
                patterns.extend([
                    f"tweet_likes:*:{user_id}",
                    f"engagement_batch:*",  # Global engagement cache for likes
                ])
            elif activity_type == "bookmark":
                patterns.append(f"bookmarked_tweets:{user_id}:*")
            elif activity_type == "share":
                patterns.append(f"shared_tweets:{user_id}:*")
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"Failed to invalidate user activity cache: {e}")

    async def invalidate_feed_refresh_cache(self, user_id: str):
        patterns = [
            f"twitter_feed:{user_id}:*",
            f"merged_feed:{user_id}:*",
            f"user_flags:{user_id}:*",
            f"following_optimized:{user_id}:*",
            f"engagement_batch:*",
            f"user_recommendations:{user_id}:*",
            f"twitter_recommendations:*",
        ]
        try:
            for pattern in patterns:
                deleted = await self.delete_pattern(pattern)
                logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
        except Exception as e:
            logger.error(f"Error invalidating feed refresh cache for user {user_id}: {e}")
            raise InternalServerError(f"Failed to invalidate feed refresh cache: {e}")

    async def invalidate_follower_removal_cache(self, user_id: str, removed_follower_id: str):
        """Comprehensive cache invalidation when a follower is removed"""
        patterns = [
            # Profile and follow relationship caches
            f"profile:{user_id}:*",
            f"profile:{removed_follower_id}:*",
            f"follow_cache:{removed_follower_id}:{user_id}:*",
            f"follow_cache:{user_id}:{removed_follower_id}:*",
            
            # Feed caches for both users
            f"twitter_feed:{user_id}:*",
            f"twitter_feed:{removed_follower_id}:*",
            f"merged_feed:{user_id}:*",
            f"merged_feed:{removed_follower_id}:*",
            
            # Follower/following list caches
            f"followers:{user_id}:*",
            f"following:{removed_follower_id}:*",
            f"new_followers:{user_id}:*",
            f"mutual_followers:{user_id}:*",
            f"mutual_followers:{removed_follower_id}:*",
            
            # User activity and engagement caches
            f"user_activity:{user_id}:follow:*",
            f"user_activity:{removed_follower_id}:follow:*",
            f"engagement_batch:*",
            
            # Recommendation caches
            f"user_recommendations:{user_id}:*",
            f"user_recommendations:{removed_follower_id}:*",
            f"twitter_recommendations:*",
            
            # User flags and metadata
            f"user_flags:{user_id}:*",
            f"user_flags:{removed_follower_id}:*",
            f"following_optimized:{removed_follower_id}:*",
        ]
        
        try:
            total_deleted = 0
            for pattern in patterns:
                deleted = await self.delete_pattern(pattern)
                total_deleted += deleted
                if deleted > 0:
                    logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
            
            logger.info(
                f"Successfully invalidated {total_deleted} cache entries for follower removal: "
                f"user {user_id} removed follower {removed_follower_id}"
            )
            
        except Exception as e:
            logger.error(
                f"Error invalidating follower removal cache for user {user_id} "
                f"removing follower {removed_follower_id}: {e}"
            )
            raise InternalServerError(f"Failed to invalidate follower removal cache: {e}")

    async def invalidate_tweet_share_cache(self, tweet_id: int, sender_id: str, recipient_ids: List[str]):
        """Comprehensive cache invalidation for tweet sharing operations"""
        patterns = [
            # Tweet engagement and response caches
            f"tweet_response:{tweet_id}:*",
            f"engagement_batch:*",
            f"engagement_velocity:*",
            
            # Sender caches
            f"sent_shared_tweets:{sender_id}:*",
            f"user_activity:{sender_id}:share:*",
            f"user_activity:{sender_id}:*",
            f"twitter_feed:{sender_id}:*",
            f"user_flags:{sender_id}:*",
        ]
        
        # Add recipient-specific patterns
        for recipient_id in recipient_ids:
            patterns.extend([
                f"received_shared_tweets:{recipient_id}:*",
                f"user_activity:{recipient_id}:share:*",
                f"user_activity:{recipient_id}:*",
                f"twitter_feed:{recipient_id}:*",
                f"user_flags:{recipient_id}:*",
                f"user_recommendations:{recipient_id}:*",
            ])
        
        # Global caches that might be affected
        patterns.extend([
            f"twitter_recommendations:*",
            f"all_user_metadata:*",
        ])
        
        try:
            total_deleted = 0
            for pattern in patterns:
                deleted = await self.delete_pattern(pattern)
                total_deleted += deleted
                if deleted > 0:
                    logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")
            
            logger.info(
                f"Successfully invalidated {total_deleted} cache entries for tweet share: "
                f"tweet {tweet_id}, sender {sender_id}, recipients {recipient_ids}"
            )
            
        except Exception as e:
            logger.error(
                f"Error invalidating tweet share cache for tweet {tweet_id}, "
                f"sender {sender_id}, recipients {recipient_ids}: {e}"
            )
            raise InternalServerError(f"Failed to invalidate tweet share cache: {e}")

    async def acquire_lock(self, key: str, ttl: int = 10) -> bool:
        """Acquire a distributed lock for cache stampede protection."""
        try:
            async with self._redis_operation("acquire_lock"):
                lock_key = versioned_key(f"lock:{key}")
                # SETNX with expiration
                result = await self._redis.set(lock_key, "1", ex=ttl, nx=True)
                return result is True
        except Exception as e:
            logger.error(f"Failed to acquire lock for {key}: {e}")
            return False

    async def release_lock(self, key: str) -> None:
        try:
            async with self._redis_operation("release_lock"):
                lock_key = versioned_key(f"lock:{key}")
                await self._redis.delete(lock_key)
        except Exception as e:
            logger.error(f"Failed to release lock for {key}: {e}")

    async def warn_if_many_deleted(self, pattern: str, deleted_count: int, threshold: int = 1000):
        if deleted_count > threshold:
            logger.warning(f"Pattern deletion for {pattern} deleted {deleted_count} keys! Consider optimizing cache key design.")

    async def invalidate_comment_cache(self, comment_id: int, tweet_id: int = None):
        """Invalidate comment-related cache"""
        try:
            patterns = [
                f"comment:{comment_id}:*",
                f"comment_response:{comment_id}:*",
                f"comment_likes:{comment_id}:*",
                f"comment_replies:{comment_id}:*",
            ]
            if tweet_id:
                patterns.extend([
                    f"tweet_comments:{tweet_id}:*",
                    f"comment_count:{tweet_id}:*",
                ])
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Invalidated comment cache for comment {comment_id}")
        except Exception as e:
            logger.error(f"Failed to invalidate comment cache for comment {comment_id}: {e}")

    async def invalidate_user_interaction_cache(self, user_id: str, interaction_type: str = "all"):
        """Invalidate user interaction cache (likes, bookmarks, shares, comments)"""
        try:
            patterns = []
            if interaction_type in ["all", "like"]:
                patterns.extend([
                    f"user_likes:{user_id}:*",
                    f"liked_tweets:{user_id}:*",
                ])
            if interaction_type in ["all", "bookmark"]:
                patterns.extend([
                    f"user_bookmarks:{user_id}:*",
                    f"bookmarked_tweets:{user_id}:*",
                ])
            if interaction_type in ["all", "share"]:
                patterns.extend([
                    f"user_shares:{user_id}:*",
                    f"shared_tweets:{user_id}:*",
                ])
            if interaction_type in ["all", "comment"]:
                patterns.extend([
                    f"user_comments:{user_id}:*",
                    f"my_comments:{user_id}:*",
                ])
            
            tasks = [self.delete_pattern(pattern) for pattern in patterns]
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"Invalidated {interaction_type} interaction cache for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to invalidate interaction cache for user {user_id}: {e}")

    async def batch_invalidate_user_feeds(self, user_ids: list[str]):
        """Batch invalidate feeds for multiple users"""
        try:
            patterns = []
            for user_id in user_ids:
                patterns.extend([
                    f"tweet_feed:{user_id}:*",
                    f"twitter_feed:{user_id}:*",
                    f"merged_feed:{user_id}:*",
                    f"recommendations:{user_id}:*",
                ])
            
            # Process in batches to avoid overwhelming Redis
            batch_size = 50
            for i in range(0, len(patterns), batch_size):
                batch = patterns[i:i + batch_size]
                tasks = [self.delete_pattern(pattern) for pattern in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info(f"Batch invalidated feeds for {len(user_ids)} users")
        except Exception as e:
            logger.error(f"Failed to batch invalidate feeds: {e}")

    async def get_cache_health(self) -> dict:
        """Get detailed cache health metrics with application metrics"""
        try:
            await self.connect()
            info = await self._redis.info()
            metrics = cache_metrics.get_stats()
            
            redis_hit_ratio = 0
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            if hits + misses > 0:
                redis_hit_ratio = hits / (hits + misses)
            
            # Sample key counts by pattern
            key_patterns = [
                "profile:*", "tweet_feed:*", "engagement:*", "followers:*", 
                "following:*", "user_tweets:*", "recommendations:*"
            ]
            
            pattern_counts = {}
            for pattern in key_patterns:
                keys = await self.keys(pattern)
                pattern_counts[pattern] = len(keys)
            
            return {
                "status": "healthy",
                "redis_info": {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory", 0),
                    "used_memory_human": info.get("used_memory_human", "0B"),
                    "keyspace_hits": hits,
                    "keyspace_misses": misses,
                    "redis_hit_ratio": redis_hit_ratio,
                    "version": info.get("redis_version", "unknown"),
                },
                "application_metrics": metrics,
                "compression_enabled": self.compression_enabled,
                "compression_threshold": self.compression_threshold,
                "key_distribution": pattern_counts,
                "cache_version": CACHE_VERSION,
            }
        except Exception as e:
            logger.error(f"Failed to get cache health: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def batch_get(self, keys: List[str]) -> dict:
        """Optimized batch get operation with monitoring"""
        try:
            cache_metrics.record_operation("batch_get")
            
            if not keys:
                return {}
            
            # Get values directly without mget to handle each key properly
            result = {}
            for key in keys:
                value = await self.get(key)
                if value is not None:
                    result[key] = value
                    
            return result
            
        except Exception as e:
            cache_metrics.record_error()
            logger.error(f"Batch get error: {e}")
            return {}

    async def batch_set_optimized(self, mapping: dict, ttl: Optional[int] = None, compress: Optional[bool] = None) -> bool:
        """Optimized batch set operation with compression support"""
        try:
            cache_metrics.record_operation("batch_set_optimized")
            
            if not mapping:
                return True
            
            # For large batches, use pipeline for better performance
            if len(mapping) > 10:
                return await self._batch_set_pipeline(mapping, ttl, compress)
            else:
                return await self.mset(mapping, ttl)
            
        except Exception as e:
            cache_metrics.record_error()
            logger.error(f"Batch set optimized error: {e}")
            return False

    async def _batch_set_pipeline(self, mapping: dict, ttl: Optional[int] = None, compress: Optional[bool] = None) -> bool:
        """Internal method for pipeline-based batch set"""
        try:
            async with self._redis_operation("batch_set_pipeline"):
                pipe = self._redis.pipeline()
                
                for key, value in mapping.items():
                    versioned_key_name = versioned_key(key)
                    
                    # Serialize the value
                    if isinstance(value, (dict, list)):
                        serialized_value = json.dumps(
                            value, separators=(",", ":"), cls=DateTimeEncoder
                        )
                    elif isinstance(value, str):
                        serialized_value = value
                    else:
                        serialized_value = json.dumps(
                            value, separators=(",", ":"), cls=DateTimeEncoder
                        )
                    
                    # Apply compression logic
                    use_compression = compress if compress is not None else (
                        self.compression_enabled and should_compress(serialized_value, self.compression_threshold)
                    )
                    
                    store_value = serialized_value
                    compression_flag = "0"
                    
                    if use_compression:
                        try:
                            original_size = len(serialized_value.encode('utf-8'))
                            compressed_data = compress_data(serialized_value)
                            compressed_size = len(compressed_data)
                            
                            if compressed_size < original_size * 0.9:
                                store_value = compressed_data
                                compression_flag = "1"
                                cache_metrics.record_compression_savings(original_size, compressed_size)
                        except Exception as e:
                            logger.warning(f"Compression failed for key {key}: {e}")
                    
                    # Store data
                    final_value = f"{compression_flag}:{store_value}" if isinstance(store_value, str) else store_value
                    
                    if ttl:
                        if isinstance(store_value, bytes):
                            # For compressed data, prepend compression flag as bytes
                            final_bytes = b"1:" + store_value
                            pipe.setex(versioned_key_name, ttl, final_bytes)
                        else:
                            # For uncompressed data, encode to bytes
                            pipe.setex(versioned_key_name, ttl, final_value.encode('utf-8'))
                    else:
                        if isinstance(store_value, bytes):
                            # For compressed data, prepend compression flag as bytes
                            final_bytes = b"1:" + store_value
                            pipe.set(versioned_key_name, final_bytes)
                        else:
                            # For uncompressed data, encode to bytes
                            pipe.set(versioned_key_name, final_value.encode('utf-8'))
                
                results = await pipe.execute()
                return all(results)
                
        except Exception as e:
            logger.error(f"Pipeline batch set error: {e}")
            return False

    async def get_metrics(self) -> dict:
        """Get detailed cache metrics"""
        return cache_metrics.get_stats()

    async def reset_metrics(self) -> bool:
        """Reset cache metrics"""
        try:
            cache_metrics.reset()
            return True
        except Exception as e:
            logger.error(f"Failed to reset metrics: {e}")
            return False

    async def cache_info(self, pattern: str = "*") -> dict:
        """Get information about cached keys matching pattern"""
        try:
            keys = await self.keys(pattern)
            info = {
                "total_keys": len(keys),
                "pattern": pattern,
                "sample_keys": keys[:10] if keys else [],
                "metrics": cache_metrics.get_stats()
            }
            
            # Get memory usage for a sample of keys
            if keys:
                sample_keys = keys[:5]
                memory_usage = 0
                for key in sample_keys:
                    try:
                        size = await self._redis.memory_usage(versioned_key(key))
                        if size:
                            memory_usage += size
                    except:
                        pass
                info["sample_memory_usage_bytes"] = memory_usage
                
            return info
            
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {"error": str(e)}


cache_service = CacheService()
