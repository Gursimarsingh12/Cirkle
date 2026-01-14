import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from user_profile.models.Interest import Interest
from user_profile.models.UserInterest import UserInterest
from auth.models.User import User
from auth.models.UserProfile import UserProfile
from caching.cache_service import cache_service
from core.config import get_settings
from core.exceptions import (
    NotFoundError,
    ValidationError,
    ConflictError,
    BaseCustomException,
)

settings = get_settings()
logger = logging.getLogger(__name__)


class InterestCruds:
    async def get_all_interests(self, db: AsyncSession) -> list:
        interests = (
            (await db.execute(select(Interest).order_by(Interest.name))).scalars().all()
        )
        return [{"id": interest.id, "name": interest.name} for interest in interests]

    async def get_user_interests(self, db: AsyncSession, user_id: str) -> list:
        user = (
            await db.execute(select(User).where(User.user_id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        if user.is_blocked or (
            user.block_until and user.block_until > datetime.now().date()
        ):
            raise ValidationError(
                "Your account has been blocked permanently. Please contact support."
            )
        user_interests = (
            (
                await db.execute(
                    select(UserInterest).where(UserInterest.user_id == user_id)
                )
            )
            .scalars()
            .all()
        )
        interest_ids = [ui.interest_id for ui in user_interests]
        interests = (
            (await db.execute(select(Interest).where(Interest.id.in_(interest_ids))))
            .scalars()
            .all()
        )
        return [{"id": interest.id, "name": interest.name} for interest in interests]

    async def get_interest_by_id(self, db: AsyncSession, interest_id: int):
        return (
            await db.execute(select(Interest).where(Interest.id == interest_id))
        ).scalar_one_or_none()

    async def set_user_interests(
        self, db: AsyncSession, user_id: str, interest_ids: list[int]
    ) -> None:
        user = (
            await db.execute(select(User).where(User.user_id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        if user.is_blocked or (
            user.block_until and user.block_until > datetime.now().date()
        ):
            raise ValidationError(
                "Your account has been blocked permanently. Please contact support."
            )
        if len(interest_ids) > 8:
            raise ValidationError("A user can have at most 8 interests.")
        interests = (
            (await db.execute(select(Interest).where(Interest.id.in_(interest_ids))))
            .scalars()
            .all()
        )
        valid_interest_ids = {i.id for i in interests}
        for iid in interest_ids:
            if iid not in valid_interest_ids:
                raise ValidationError(f"Interest id '{iid}' is not valid")
        await db.execute(delete(UserInterest).where(UserInterest.user_id == user_id))
        for iid in interest_ids:
            db.add(UserInterest(user_id=user_id, interest_id=iid))
        profile = (
            await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        ).scalar_one_or_none()
        if profile:
            profile.updated_at = datetime.now()
        await db.commit()
        logger.info(f"Set interests {interest_ids} for user {user_id}")
        try:
            await cache_service.invalidate_profile_cache(user_id)
            await cache_service.invalidate_interests_cache(user_id)
            logger.info(
                f"Invalidated caches for user {user_id} after setting interests"
            )
        except BaseCustomException as e:
            logger.error(
                f"Failed to invalidate caches for user {user_id} after setting interests: {e}"
            )
            raise

    async def remove_user_interests(
        self, db: AsyncSession, user_id: str, interest_ids: list[int]
    ) -> None:
        user = (
            await db.execute(select(User).where(User.user_id == user_id))
        ).scalar_one_or_none()
        if not user:
            raise NotFoundError("User not found")
        if user.is_blocked or (
            user.block_until and user.block_until > datetime.now().date()
        ):
            raise ValidationError(
                "Your account has been blocked permanently. Please contact support."
            )
        await db.execute(
            delete(UserInterest).where(
                UserInterest.user_id == user_id,
                UserInterest.interest_id.in_(interest_ids),
            )
        )
        profile = (
            await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
        ).scalar_one_or_none()
        if profile:
            profile.updated_at = datetime.now()
        await db.commit()
        logger.info(f"Removed interests {interest_ids} for user {user_id}")
        try:
            await cache_service.invalidate_profile_cache(user_id)
            await cache_service.invalidate_interests_cache(user_id)
            logger.info(
                f"Invalidated caches for user {user_id} after removing interests"
            )
        except BaseCustomException as e:
            logger.error(
                f"Failed to invalidate caches for user {user_id} after removing interests: {e}"
            )
            raise


interest_service = InterestCruds()
