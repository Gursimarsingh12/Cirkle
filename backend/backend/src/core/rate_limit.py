import logging
from core.config import get_settings
from core.exceptions import RateLimitError, create_http_exception
from caching.cache_service import cache_service
from fastapi import Request
from functools import wraps
from core.logging import setup_logging
import json
import time

setup_logging()
logger = logging.getLogger("rate_limit")
settings = get_settings()

def rate_limit(requests_per_minute: int = None, scope: str = "ip"):
    limit = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            user_id = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request:
                return await func(*args, **kwargs)
            if 'current_user' in kwargs:
                user_id = kwargs['current_user']
            elif hasattr(request, 'state') and hasattr(request.state, 'user_id'):
                user_id = getattr(request.state, 'user_id')
            client_ip = request.client.host
            endpoint = f"{request.method}:{request.url.path}"
            now = int(time.time())
            window = 60
            reset = now - (now % window) + window
            if scope == "user" and user_id:
                cache_key = f"rate_limit:user:{user_id}:{endpoint}"
            elif scope == "global":
                cache_key = f"rate_limit:global:{endpoint}"
            else:
                cache_key = f"rate_limit:{client_ip}:{endpoint}"
            try:
                current_requests = await cache_service.get(cache_key) or 0
                remaining = max(0, limit - int(current_requests))
                if int(current_requests) >= limit:
                    logger.warning(json.dumps({"event": "rate_limit_exceeded", "scope": scope, "key": cache_key, "limit": limit}))
                    headers = {
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset)
                    }
                    raise create_http_exception(RateLimitError(f"Rate limit exceeded. Max {limit} requests per minute."), headers=headers)
                await cache_service.set(cache_key, int(current_requests) + 1, window)
                response = await func(*args, **kwargs)
                if hasattr(response, "headers"):
                    response.headers["X-RateLimit-Limit"] = str(limit)
                    response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
                    response.headers["X-RateLimit-Reset"] = str(reset)
                return response
            except RateLimitError:
                raise
            except Exception as e:
                logger.error(json.dumps({"event": "rate_limit_error", "error": str(e), "scope": scope, "key": cache_key}))
                return await func(*args, **kwargs)
        return wrapper
    return decorator