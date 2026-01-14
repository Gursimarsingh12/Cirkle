import asyncio
import logging
import sys
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from auth.routes.AuthRouters import router as auth_router
from auth.middleware.AuthMiddleware import (
    security_headers_middleware,
    request_logging_middleware,
)
from caching.cache_service import cache_service
from core.config import get_settings
from core.logging import setup_logging
from core.exceptions import (
    BaseCustomException,
    custom_exception_handler,
    general_exception_handler,
)
from core.middleware import add_request_id_middleware
from database.base import Base
from database.session import engine
from user_profile.routes.ProfileRouters import router as profile_router
from tweets.routes.TweetRouters import router as tweet_router
from admin.routes.AdminRouters import router as admin_router
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.exc import OperationalError

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


async def create_tables():
    """Create database tables with retry logic for concurrent access"""
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all, checkfirst=True)
            logger.info(f"✅ Database tables created/verified successfully")
            return
        except OperationalError as e:
            error_msg = str(e)
            if "already exists" in error_msg or "being modified by concurrent" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)
                    logger.warning(f"⚠️  Database conflict detected (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.info("ℹ️  Database tables already exist, continuing...")
                    return
            else:
                logger.error(f"❌ Database creation failed: {e}")
                raise
        except Exception as e:
            logger.error(f"❌ Unexpected error during table creation: {e}")
            raise


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="cirkle's API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.mount("/image", StaticFiles(directory="user"), name="image")

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "*",
        ]
        if settings.DEBUG
        else []
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(security_headers_middleware)
app.middleware("http")(request_logging_middleware)
add_request_id_middleware(app)
app.add_exception_handler(BaseCustomException, custom_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


async def startup_event():
    try:
        await create_tables()
        await cache_service.connect()
        logger.info(
            f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started successfully"
        )
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        sys.exit(1)


async def shutdown_event():
    await cache_service.disconnect()
    logger.info("🛑 Application shutdown complete")
    if isinstance(engine, AsyncEngine):
        await engine.dispose()


app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
    try:
        await cache_service.set("health_check", "ok", 10)
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1 as health_check"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    health_status["dependencies"] = {"redis": redis_status, "database": db_status}
    return health_status


app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(tweet_router)
app.include_router(admin_router)


@app.get("/health/recommendation", tags=["Health"])
async def recommendation_system_health():
    try:
        recommendation_config = await cache_service.get("production_recommendation_config")
        recommendation_monitoring = await cache_service.get("recommendation_monitoring")
        
        status = {
            "status": "healthy",
            "recommendation_system": {
                "enabled": recommendation_config.get("recommendation_enabled", False) if recommendation_config else False,
                "percentage_distribution": recommendation_config.get("percentage_distribution", {}) if recommendation_config else {},
                "cache_ttl_settings": {
                    "feed_cache_ttl": recommendation_config.get("feed_cache_ttl", 300),
                    "user_metadata_ttl": recommendation_config.get("user_metadata_ttl", 1800),
                    "engagement_cache_ttl": recommendation_config.get("engagement_cache_ttl", 600),
                } if recommendation_config else {},
                "production_ready": recommendation_monitoring.get("production_ready", False) if recommendation_monitoring else False,
                "last_optimized": recommendation_monitoring.get("last_optimized", "never") if recommendation_monitoring else "never",
                "cache_warming_completed": recommendation_monitoring.get("cache_warming_completed", False) if recommendation_monitoring else False,
            }
        }
        
        if not recommendation_config:
            status["status"] = "degraded"
            status["message"] = "Recommendation system not configured"
        elif not recommendation_monitoring:
            status["status"] = "degraded"
            status["message"] = "Recommendation system monitoring not set up"
        
        return status
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "recommendation_system": {
                "enabled": False,
                "production_ready": False,
            }
        }


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "features": {
            "recommendation_system": "enabled",
            "percentage_based_distribution": "40%, 20%, 5%, 5%, 15%, 15%",
            "priority_categories": [
                "Prime + Organizational + Engagement (40%)",
                "Prime + Organizational + No Engagement (20%)",
                "Prime + Following + Engagement (5%)",
                "Prime + Following + No Engagement (5%)",
                "Following + Engagement (15%)",
                "Following + No Engagement (15%)"
            ]
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app", host="localhost", port=8000, reload=settings.DEBUG, log_level="info"
    )
