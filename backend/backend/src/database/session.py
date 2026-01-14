from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import event, text
from core.config import get_settings
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=50,
    max_overflow=100,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_timeout=30,
    echo=False,
    echo_pool=settings.DEBUG,
    future=True,
    connect_args=(
        {
            "charset": "utf8mb4",
            "autocommit": False,
            "connect_timeout": 60,
        }
        if "mysql" in settings.DATABASE_URL
        else {}
    ),
    execution_options={
        "isolation_level": "READ_COMMITTED",
        "compiled_cache": {},
    },
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    query_cls=None,
)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    session = None
    try:
        session = AsyncSessionLocal()
        if "mysql" in settings.DATABASE_URL:
            await session.execute(
                text(
                    "SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'"
                )
            )
        elif "postgresql" in settings.DATABASE_URL:
            await session.execute(text("SET statement_timeout = '10s'"))
        yield session
    except Exception as e:
        if session:
            await session.rollback()
        logger.error(f"❌ Database session error: {e}")
        raise
    finally:
        if session:
            await session.close()


async def get_read_only_session() -> AsyncGenerator[AsyncSession, None]:
    session = None
    try:
        session = AsyncSessionLocal()
        if "mysql" in settings.DATABASE_URL:
            await session.execute(
                text(
                    "SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO'"
                )
            )
            await session.execute(text("SET SESSION read_only = 1"))
        elif "postgresql" in settings.DATABASE_URL:
            await session.execute(text("SET default_transaction_read_only = on"))
            await session.execute(text("SET statement_timeout = '5s'"))
        yield session
    except Exception as e:
        if session:
            await session.rollback()
        logger.error(f"❌ Read-only session error: {e}")
        raise
    finally:
        if session:
            await session.close()


async def check_database_health() -> dict:
    try:
        pool = engine.pool
        return {
            "status": "healthy",
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "checked_in": pool.checkedin(),
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


async def close_database_connections():
    try:
        await engine.dispose()
        logger.info("✅ Database connections closed gracefully")
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")
