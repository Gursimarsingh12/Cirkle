from fastapi import Request
from core.config import get_settings
import time
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

async def request_logging_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host
    method = request.method
    url = str(request.url)
    logger.info(f"🔄 {method} {url} from {client_ip}")
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"✅ {method} {url} - {response.status_code} ({process_time:.3f}s)")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ {method} {url} - Error: {str(e)} ({process_time:.3f}s)")
        raise