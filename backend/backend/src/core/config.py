from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = os.getenv("APP_NAME", "cirkle")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "TRUE").upper() == "TRUE"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+aiomysql://root:rootpassword@mysql:3307/dbname")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", 20))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", 0))
    DATABASE_POOL_TIMEOUT: int = int(os.getenv("DATABASE_POOL_TIMEOUT", 30))
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_POOL_SIZE: int = int(os.getenv("REDIS_POOL_SIZE", 20))
    REDIS_TIMEOUT: int = int(os.getenv("REDIS_TIMEOUT", 5))
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", 8))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    BCRYPT_ROUNDS: int = int(os.getenv("BCRYPT_ROUNDS", 12))
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", 8))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", "")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    PROFILE_CACHE_TTL: int = int(os.getenv("PROFILE_CACHE_TTL", 3600))
    INTERESTS_CACHE_TTL: int = int(os.getenv("INTERESTS_CACHE_TTL", 3600))
    FOLLOW_CACHE_TTL: int = int(os.getenv("FOLLOW_CACHE_TTL", 3600))
    FOLLOW_REQUESTS_CACHE_TTL: int = int(os.getenv("FOLLOW_REQUESTS_CACHE_TTL", 3600))
    COUNTS_CACHE_TTL: int = int(os.getenv("COUNTS_CACHE_TTL", 3600))
    MAX_TWEET_IMAGES: int = int(os.getenv("MAX_TWEET_IMAGES", 4))
    MAX_TWEET_IMAGE_SIZE_MB: int = int(os.getenv("MAX_TWEET_IMAGE_SIZE_MB", 10))
    TWEET_CACHE_TTL: int = int(os.getenv("TWEET_CACHE_TTL", 60))
    TWEET_PAGE_SIZE: int = int(os.getenv("TWEET_PAGE_SIZE", 20))
    RECOMMENDATION_CACHE_TTL: int = int(os.getenv("RECOMMENDATION_CACHE_TTL", 300))
    
    # NEW: Recommendation System Configuration
    RECOMMENDATION_ENABLED: bool = os.getenv("RECOMMENDATION_ENABLED", "TRUE").upper() == "TRUE"
    RECOMMENDATION_PRIME_ORG_WITH_ENGAGEMENT_PERCENT: int = int(os.getenv("RECOMMENDATION_PRIME_ORG_WITH_ENGAGEMENT_PERCENT", 40))
    RECOMMENDATION_PRIME_ORG_WITHOUT_ENGAGEMENT_PERCENT: int = int(os.getenv("RECOMMENDATION_PRIME_ORG_WITHOUT_ENGAGEMENT_PERCENT", 20))
    RECOMMENDATION_PRIME_FOLLOWING_WITH_ENGAGEMENT_PERCENT: int = int(os.getenv("RECOMMENDATION_PRIME_FOLLOWING_WITH_ENGAGEMENT_PERCENT", 5))
    RECOMMENDATION_PRIME_FOLLOWING_WITHOUT_ENGAGEMENT_PERCENT: int = int(os.getenv("RECOMMENDATION_PRIME_FOLLOWING_WITHOUT_ENGAGEMENT_PERCENT", 5))
    RECOMMENDATION_FOLLOWING_WITH_ENGAGEMENT_PERCENT: int = int(os.getenv("RECOMMENDATION_FOLLOWING_WITH_ENGAGEMENT_PERCENT", 15))
    RECOMMENDATION_FOLLOWING_WITHOUT_ENGAGEMENT_PERCENT: int = int(os.getenv("RECOMMENDATION_FOLLOWING_WITHOUT_ENGAGEMENT_PERCENT", 15))
    RECOMMENDATION_MAX_TWEETS_LIMIT: int = int(os.getenv("RECOMMENDATION_MAX_TWEETS_LIMIT", 2000))
    RECOMMENDATION_QUERY_TIMEOUT: int = int(os.getenv("RECOMMENDATION_QUERY_TIMEOUT", 5))
    
    COMMENT_PAGE_SIZE: int = int(os.getenv("COMMENT_PAGE_SIZE", 20))
    COMMENT_CACHE_TTL: int = int(os.getenv("COMMENT_CACHE_TTL", 300))
    SHARE_CACHE_TTL: int = int(os.getenv("SHARE_CACHE_TTL", 300))
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Production Optimization Flags
    ENABLE_PRODUCTION_OPTIMIZATIONS: bool = os.getenv("ENABLE_PRODUCTION_OPTIMIZATIONS", "TRUE").upper() == "TRUE"
    ENABLE_CACHE_WARMING: bool = os.getenv("ENABLE_CACHE_WARMING", "TRUE").upper() == "TRUE"
    ENABLE_PERFORMANCE_MONITORING: bool = os.getenv("ENABLE_PERFORMANCE_MONITORING", "TRUE").upper() == "TRUE"
    ENABLE_RECOMMENDATION_METRICS: bool = os.getenv("ENABLE_RECOMMENDATION_METRICS", "TRUE").upper() == "TRUE"

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()