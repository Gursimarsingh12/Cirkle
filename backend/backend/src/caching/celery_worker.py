from celery import Celery
import asyncio
from tweets.cruds.TweetCruds import tweet_service
from database.session import AsyncSessionLocal
from user_profile.models.Follower import Follower
import os

celery_app = Celery(
    "tasks",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def refresh_user_feed(self, user_id: str, page: int = 1):
    try:
        asyncio.run(_refresh_feed(user_id, page))
    except Exception as exc:
        raise self.retry(exc=exc)

async def _refresh_feed(user_id: str, page: int):
    async with AsyncSessionLocal() as db:
        await tweet_service.get_tweet_feed(db, user_id, page)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def refresh_user_recommend(self, user_id: str, page: int = 1):
    try:
        asyncio.run(_refresh_recommend(user_id, page))
    except Exception as exc:
        raise self.retry(exc=exc)

async def _refresh_recommend(user_id: str, page: int):
    async with AsyncSessionLocal() as db:
        await tweet_service.get_recommended_tweets(db, user_id, page)

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def refresh_followers_feeds(self, user_id: str, page: int = 1):
    try:
        asyncio.run(_refresh_followers_feeds(user_id, page))
    except Exception as exc:
        raise self.retry(exc=exc)
    
async def _refresh_followers_feeds(user_id: str, page: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            Follower.__table__.select().where(Follower.followee_id == user_id)
        )
        followers = result.fetchall()
        for row in followers:
            follower_id = row.follower_id
            await tweet_service.get_tweet_feed(db, follower_id, page)