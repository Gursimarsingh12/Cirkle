# Centralized Cache Configuration
# This file standardizes TTL values and cache patterns across all CRUDs

from enum import Enum


class CacheConstants:
    """Standardized cache TTL values"""
    
    # Core Data Types
    PROFILE_TTL = 1800          # 30 minutes - User profiles
    SOCIAL_GRAPH_TTL = 1800     # 30 minutes - Follow/following relationships
    FEED_TTL = 600              # 10 minutes - Tweet feeds
    ENGAGEMENT_TTL = 300        # 5 minutes - Likes, comments, shares
    
    # Expensive Queries  
    EXPENSIVE_QUERY_TTL = 3600  # 1 hour - Complex aggregations
    RECOMMENDATION_TTL = 1800   # 30 minutes - AI/ML recommendations
    SEARCH_TTL = 900            # 15 minutes - Search results
    
    # Real-time Data
    ACTIVITY_TTL = 300          # 5 minutes - Recent activity
    NOTIFICATIONS_TTL = 180     # 3 minutes - Notifications
    PRESENCE_TTL = 60           # 1 minute - Online status
    
    # Media and Static Content
    MEDIA_TTL = 7200           # 2 hours - Media metadata
    USER_CONTENT_TTL = 3600    # 1 hour - User generated content
    
    # Temporary/Session Data
    SESSION_TTL = 900          # 15 minutes - Session cache
    TEMP_TTL = 300             # 5 minutes - Temporary data
    
    # Empty Results (shorter to allow recovery)
    EMPTY_RESULT_TTL = 180     # 3 minutes - Empty query results
    
    # Lock TTLs for cache stampede protection
    LOCK_TTL_SHORT = 10        # 10 seconds - Quick operations
    LOCK_TTL_MEDIUM = 30       # 30 seconds - Medium operations  
    LOCK_TTL_LONG = 60         # 60 seconds - Expensive operations


class CacheKeyPatterns:
    """Standardized cache key patterns to prevent collisions"""
    
    # User related
    PROFILE = "profile:{user_id}:req:{requester_id}"
    PROFILE_PUBLIC = "profile_pub:{user_id}" 
    USER_METADATA = "user_meta:{user_id}"
    
    # Social graph
    FOLLOWERS = "followers:{user_id}:p{page}:req:{requester_id}"
    FOLLOWING = "following:{user_id}:p{page}"
    MUTUAL_FOLLOWERS = "mutual:{user1}:{user2}"
    FOLLOW_REQUESTS = "follow_req:{user_id}"
    
    # Feed and content
    FEED = "feed:{user_id}:p{page}:type{feed_type}:inc{include_rec}"
    TWEET = "tweet:{tweet_id}:req:{requester_id}"
    COMMENTS = "comments:{tweet_id}:p{page}:req:{requester_id}"
    ENGAGEMENT = "engagement:{tweet_id}"
    
    # Sharing
    SHARE_CHAT_LIST = "share_list:{user_id}:p{page}"
    SHARE_CONVERSATION = "share_conv:{user1}:{user2}:p{page}"
    
    # Search and discovery
    USER_SEARCH = "search_user:{query_hash}:p{page}"
    RECOMMENDATIONS = "recommend:{user_id}:type{type}:p{page}"
    TOP_ACCOUNTS = "top_accounts:{limit}"
    
    # Aggregations
    USER_STATS = "stats:{user_id}:type{type}"
    ENGAGEMENT_COUNTS = "eng_counts:{tweet_ids_hash}"
    VELOCITY_SCORES = "velocity:{tweet_ids_hash}"


class CacheStrategies(Enum):
    """Cache strategy types for different operations"""
    
    CACHE_FIRST = "cache_first"          # Try cache first, compute if miss
    CACHE_ASIDE = "cache_aside"          # Compute then cache
    WRITE_THROUGH = "write_through"      # Update cache and DB together
    WRITE_BEHIND = "write_behind"        # Update cache, async DB update
    CACHE_ONLY = "cache_only"            # Cache-only data (computed)


class CacheSettings:
    """Cache behavior settings"""
    
    # Stampede protection
    ENABLE_LOCK_PROTECTION = True
    MAX_LOCK_WAIT_TIME = 5.0  # seconds
    
    # Error handling
    GRACEFUL_DEGRADATION = True
    LOG_CACHE_ERRORS = True
    CACHE_ERROR_THRESHOLD = 10  # failures per minute before alerting
    
    # Performance tuning
    BATCH_SIZE = 100           # Max items in batch operations
    MAX_KEY_LENGTH = 250       # Redis key length limit
    COMPRESS_LARGE_OBJECTS = True
    COMPRESSION_THRESHOLD = 1024  # bytes
    
    # Monitoring
    ENABLE_METRICS = True
    METRICS_SAMPLE_RATE = 0.1  # 10% sampling for detailed metrics
    
    # Cache warming
    ENABLE_WARM_UP = True
    WARM_UP_BATCH_SIZE = 50
    WARM_UP_DELAY = 0.1        # seconds between batch warm-ups


def get_ttl_for_operation(operation_type: str, data_size: int = 0, is_empty: bool = False) -> int:
    """
    Get appropriate TTL for an operation based on type and characteristics
    
    Args:
        operation_type: Type of operation (profile, feed, etc.)
        data_size: Size of data being cached
        is_empty: Whether the result is empty
        
    Returns:
        TTL in seconds
    """
    if is_empty:
        return CacheConstants.EMPTY_RESULT_TTL
        
    base_ttl = {
        'profile': CacheConstants.PROFILE_TTL,
        'social_graph': CacheConstants.SOCIAL_GRAPH_TTL,
        'feed': CacheConstants.FEED_TTL,
        'engagement': CacheConstants.ENGAGEMENT_TTL,
        'expensive_query': CacheConstants.EXPENSIVE_QUERY_TTL,
        'recommendation': CacheConstants.RECOMMENDATION_TTL,
        'search': CacheConstants.SEARCH_TTL,
        'activity': CacheConstants.ACTIVITY_TTL,
        'media': CacheConstants.MEDIA_TTL,
        'session': CacheConstants.SESSION_TTL,
        'temp': CacheConstants.TEMP_TTL,
    }.get(operation_type, CacheConstants.TEMP_TTL)
    
    # Adjust TTL based on data size (larger data cached longer)
    if data_size > 10000:  # Large objects
        return min(base_ttl * 2, CacheConstants.EXPENSIVE_QUERY_TTL)
    elif data_size < 100:  # Small objects
        return max(base_ttl // 2, CacheConstants.ACTIVITY_TTL)
    
    return base_ttl


def get_cache_key(pattern: str, **kwargs) -> str:
    """
    Generate cache key from pattern with proper escaping and validation
    
    Args:
        pattern: Cache key pattern from CacheKeyPatterns
        **kwargs: Values to substitute in pattern
        
    Returns:
        Formatted cache key
        
    Raises:
        ValueError: If key would exceed max length
    """
    # Ensure all values are strings and safe
    safe_kwargs = {}
    for key, value in kwargs.items():
        if value is None:
            safe_kwargs[key] = "none"
        elif isinstance(value, bool):
            safe_kwargs[key] = "true" if value else "false"
        else:
            # Remove dangerous characters and limit length
            safe_value = str(value).replace(':', '_').replace('*', '_')[:50]
            safe_kwargs[key] = safe_value
    
    try:
        cache_key = pattern.format(**safe_kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required parameter for cache key: {e}")
    
    if len(cache_key) > CacheSettings.MAX_KEY_LENGTH:
        raise ValueError(f"Cache key too long: {len(cache_key)} > {CacheSettings.MAX_KEY_LENGTH}")
    
    return cache_key


def should_use_lock(operation_type: str, estimated_compute_time: float = 0) -> bool:
    """
    Determine if cache stampede protection should be used
    
    Args:
        operation_type: Type of operation
        estimated_compute_time: Expected computation time in seconds
        
    Returns:
        Whether to use locking
    """
    if not CacheSettings.ENABLE_LOCK_PROTECTION:
        return False
    
    # Use locks for expensive operations
    expensive_operations = {'feed', 'expensive_query', 'recommendation', 'search'}
    if operation_type in expensive_operations:
        return True
    
    # Use locks for operations taking > 1 second
    if estimated_compute_time > 1.0:
        return True
        
    return False


def get_lock_ttl(operation_type: str, estimated_compute_time: float = 0) -> int:
    """Get appropriate lock TTL for operation"""
    if estimated_compute_time > 30:
        return CacheConstants.LOCK_TTL_LONG
    elif estimated_compute_time > 5:
        return CacheConstants.LOCK_TTL_MEDIUM
    else:
        return CacheConstants.LOCK_TTL_SHORT 