from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from rag.config.settings import get_settings


@lru_cache(maxsize=1)
def _get_engine():
    """Create the SQLAlchemy engine lazily so importing this module
    does not require POSTGRES_PASSWORD to be set (e.g. during tests)."""
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_recycle=settings.db_pool_recycle,
    )


@lru_cache(maxsize=1)
def _get_session_factory():
    return async_sessionmaker(_get_engine(), expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _get_session_factory()() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
