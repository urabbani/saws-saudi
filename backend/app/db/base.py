"""
SAWS Database Configuration

Database session management and base model setup.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# Create async engine
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,  # Verify connections before using
)

# Create async session maker
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    All models should inherit from this class to get:
    - Common table configuration
    - Automatic timestamp columns
    - Standard serialization methods
    """

    pass


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for dependency injection.

    Yields an async database session and ensures cleanup.

    Yields:
        AsyncSession: Database session
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database.

    Creates all tables if they don't exist.
    Use Alembic for migrations in production.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await async_engine.dispose()
