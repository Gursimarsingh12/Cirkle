from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import engine
import logging

logger = logging.getLogger(__name__)
CRITICAL_INDEXES = [
    """
    CREATE INDEX idx_tweets_created_at_user_id 
    ON tweets (created_at DESC, user_id)
    """,
    """
    CREATE INDEX idx_tweets_user_id_created_at 
    ON tweets (user_id, created_at DESC)
    """,
    """
    CREATE INDEX idx_tweets_recent_recommendations 
    ON tweets (created_at DESC, view_count DESC)
    """,
    """
    CREATE INDEX idx_followers_follower_id 
    ON followers (follower_id)
    """,
    """
    CREATE INDEX idx_followers_followee_id 
    ON followers (followee_id)
    """,
    """
    CREATE INDEX idx_followers_mutual 
    ON followers (follower_id, followee_id)
    """,
    """
    CREATE INDEX idx_user_profiles_priority 
    ON user_profiles (is_organizational, is_prime, user_id)
    """,
    """
    CREATE INDEX idx_user_profiles_user_id 
    ON user_profiles (user_id)
    """,
    """
    CREATE INDEX idx_users_active_not_blocked 
    ON users (user_id, is_blocked, is_active)
    """,
    """
    CREATE INDEX idx_users_privacy 
    ON users (user_id, is_private, is_blocked)
    """,
    """
    CREATE INDEX idx_tweet_likes_tweet_id 
    ON tweet_likes (tweet_id)
    """,
    """
    CREATE INDEX idx_tweet_likes_user_tweet 
    ON tweet_likes (user_id, tweet_id)
    """,
    """
    CREATE INDEX idx_comments_tweet_id_parent 
    ON comments (tweet_id, parent_comment_id)
    """,
    """
    CREATE INDEX idx_bookmarks_tweet_id 
    ON bookmarks (tweet_id)
    """,
    """
    CREATE INDEX idx_bookmarks_user_tweet 
    ON bookmarks (user_id, tweet_id)
    """,
    """
    CREATE INDEX idx_shares_tweet_id 
    ON shares (tweet_id)
    """,
    """
    CREATE INDEX idx_shares_user_recipient_time 
    ON shares (user_id, recipient_id, shared_at DESC)
    """,
    """
    CREATE INDEX idx_shares_recipient_user_time 
    ON shares (recipient_id, user_id, shared_at DESC)
    """,
    """
    CREATE INDEX idx_shares_conversation_time 
    ON shares (shared_at DESC, user_id, recipient_id)
    """,
    """
    CREATE INDEX idx_tweet_media_tweet_id 
    ON tweet_media (tweet_id)
    """,
]
COMPOSITE_INDEXES = [
    """
    CREATE INDEX idx_tweets_feed_optimization 
    ON tweets (created_at DESC, user_id, view_count DESC)
    """,
    """
    CREATE INDEX idx_users_profile_privacy 
    ON users (user_id, is_private, is_blocked, created_at)
    """,
    """
    CREATE INDEX idx_tweets_engagement 
    ON tweets (id, user_id, created_at, view_count)
    """,
]
PARTIAL_INDEXES = []
ANALYZE_QUERIES = [
    "ANALYZE TABLE tweets",
    "ANALYZE TABLE users",
    "ANALYZE TABLE user_profiles",
    "ANALYZE TABLE followers",
    "ANALYZE TABLE tweet_likes",
    "ANALYZE TABLE comments",
    "ANALYZE TABLE bookmarks",
    "ANALYZE TABLE shares",
    "ANALYZE TABLE tweet_media",
]


async def create_production_indexes():
    logger.info("🚀 Starting production index creation for 40,000+ users...")

    async def index_exists(session, index_name, table_name):
        query = (
            "SELECT COUNT(*) FROM information_schema.statistics "
            "WHERE table_schema = DATABASE() "
            "AND table_name = :table_name "
            "AND index_name = :index_name"
        )
        result = await session.execute(
            text(query), {"table_name": table_name, "index_name": index_name}
        )
        return result.scalar() > 0

    async with AsyncSession(engine) as session:
        try:
            logger.info("📊 Creating critical indexes...")
            for i, index_sql in enumerate(CRITICAL_INDEXES, 1):
                try:
                    lines = index_sql.strip().split("\n")
                    create_line = [line for line in lines if "CREATE INDEX" in line][0]
                    index_name = create_line.split()[2]
                    table_line = [line for line in lines if "ON " in line][0]
                    table_name = table_line.split()[1]
                    if await index_exists(session, index_name, table_name):
                        logger.info(f"⚠️  Index {index_name} already exists, skipping")
                        continue
                    sql_str = index_sql.strip().replace("\n", " ")
                    logger.info(f"Executing SQL: {sql_str}")
                    await session.execute(text(index_sql))
                    await session.commit()
                    logger.info(
                        f"✅ Created critical index {i}/{len(CRITICAL_INDEXES)}: {index_name}"
                    )
                except Exception as e:
                    logger.warning(f"⚠️  Index {i} failed: {e}")
                    await session.rollback()
            logger.info("🔗 Creating composite indexes...")
            for i, index_sql in enumerate(COMPOSITE_INDEXES, 1):
                try:
                    lines = index_sql.strip().split("\n")
                    create_line = [line for line in lines if "CREATE INDEX" in line][0]
                    index_name = create_line.split()[2]
                    table_line = [line for line in lines if "ON " in line][0]
                    table_name = table_line.split()[1]
                    if await index_exists(session, index_name, table_name):
                        logger.info(f"⚠️  Index {index_name} already exists, skipping")
                        continue
                    sql_str = index_sql.strip().replace("\n", " ")
                    logger.info(f"Executing SQL: {sql_str}")
                    await session.execute(text(index_sql))
                    await session.commit()
                    logger.info(
                        f"✅ Created composite index {i}/{len(COMPOSITE_INDEXES)}: {index_name}"
                    )
                except Exception as e:
                    logger.warning(f"⚠️  Composite index {i} failed: {e}")
                    await session.rollback()
            logger.info("⚡ Skipping partial indexes (not supported in MySQL)")
            logger.info("📈 Updating table statistics...")
            for query in ANALYZE_QUERIES:
                try:
                    logger.info(f"Executing SQL: {query}")
                    await session.execute(text(query))
                    await session.commit()
                    logger.info(f"✅ Analyzed: {query}")
                except Exception as e:
                    logger.warning(f"⚠️  Analyze failed for {query}: {e}")
                    await session.rollback()
            logger.info("🎉 Production indexes created successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")
            await session.rollback()
            raise


async def check_index_usage():
    logger.info("📊 Checking index usage statistics...")
    usage_query = (
        "SELECT "
        "TABLE_SCHEMA as schemaname,"
        "TABLE_NAME as tablename,"
        "INDEX_NAME as indexname,"
        "CARDINALITY,"
        "INDEX_TYPE "
        "FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA = DATABASE() "
        "AND TABLE_NAME IN ('tweets', 'users', 'user_profiles', 'followers', 'tweet_likes', 'comments', 'bookmarks') "
        "AND INDEX_NAME != 'PRIMARY' "
        "ORDER BY TABLE_NAME, INDEX_NAME;"
    )
    async with AsyncSession(engine) as session:
        try:
            result = await session.execute(text(usage_query))
            rows = result.fetchall()
            logger.info("Index Usage Report:")
            for row in rows:
                logger.info(
                    f"  {row.tablename}.{row.indexname}: {row.INDEX_TYPE}, cardinality: {row.CARDINALITY}"
                )
        except Exception as e:
            logger.warning(f"⚠️  Could not check index usage: {e}")


async def optimize_for_production():
    logger.info("🔧 Starting full production optimization...")
    mysql_optimizations = [
        "SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'",
        "SET SESSION optimizer_search_depth = 62",
        "SET SESSION optimizer_prune_level = 1",
        "SET SESSION optimizer_switch = 'index_merge=on,index_merge_union=on,index_merge_sort_union=on'",
    ]
    async with AsyncSession(engine) as session:
        for setting in mysql_optimizations:
            try:
                logger.info(f"Executing SQL: {setting}")
                await session.execute(text(setting))
                logger.info(f"✅ Applied: {setting}")
            except Exception as e:
                logger.warning(f"⚠️  Could not apply {setting}: {e}")
        await session.commit()
    await create_production_indexes()
    await check_index_usage()
    logger.info("🎯 Production optimization completed!")


if __name__ == "__main__":
    import asyncio

    asyncio.run(optimize_for_production())
