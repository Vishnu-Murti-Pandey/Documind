"""
Asynchronous SQLAlchemy database configuration.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import (
    DATABASE_ECHO,
    DATABASE_MAX_OVERFLOW,
    DATABASE_POOL_SIZE,
    DATABASE_URL,
)
from app.db.base import Base

# Import all models so Base.metadata contains every table.
from app.db import models  # noqa: F401


if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured."
    )


# ============================================================
# Async Engine
# ============================================================

engine = create_async_engine(
    DATABASE_URL,
    echo=DATABASE_ECHO,
    pool_pre_ping=True,
    pool_size=DATABASE_POOL_SIZE,
    max_overflow=DATABASE_MAX_OVERFLOW,
    pool_recycle=1800,
)


# ============================================================
# Session Factory
# ============================================================

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def create_database_tables() -> None:
    """
    Create missing database tables.

    Suitable for local development and the initial application
    version. It does not migrate existing table structures.
    """

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )


async def drop_database_tables() -> None:
    """
    Drop all application tables.

    Use only for local development or tests.
    """

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.drop_all
        )


async def get_db_session(
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide one database session per FastAPI request.
    """

    async with AsyncSessionFactory() as session:
        try:
            yield session

        except Exception:
            await session.rollback()
            raise

        finally:
            await session.close()


async def dispose_engine() -> None:
    """
    Close the SQLAlchemy connection pool.
    """

    await engine.dispose()
