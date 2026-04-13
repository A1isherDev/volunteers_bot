import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.database.base import Base

logger = logging.getLogger(__name__)

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _engine, _session_factory
    if _session_factory is None:
        settings = get_settings()
        url = settings.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        connect_args = {}
        if "sqlite" in url:
            connect_args["check_same_thread"] = False
        _engine = create_async_engine(
            url,
            echo=False,
            connect_args=connect_args,
        )
        _session_factory = async_sessionmaker(
            _engine,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info("Database engine created for URL scheme: %s", url.split(":")[0])
    return _session_factory


async def init_db() -> None:
    get_session_factory()
    assert _engine is not None
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = get_session_factory()
    async with factory() as session:
        from app.database.bootstrap import bootstrap_defaults

        await bootstrap_defaults(session)
        await session.commit()
    logger.info("Database tables ensured")
