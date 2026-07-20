import sys
import types

import pytest

# libchromaprint is a native dependency that is not present in every dev
# environment. app.services.audio_service imports chromaprint at module scope,
# so stub it before any app import to keep the non-audio tests runnable.
try:  # pragma: no cover - depends on the host
    import chromaprint  # noqa: F401
except Exception:  # pragma: no cover
    sys.modules["chromaprint"] = types.ModuleType("chromaprint")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session():
    """Yields a session, or skips the test when no database is reachable.

    Builds a fresh NullPool engine per test: pytest-asyncio runs each test on
    its own event loop, and a pooled asyncpg connection cannot cross loops.
    """
    from sqlalchemy import text
    from sqlalchemy.pool import NullPool
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

    from app.configs.settings import settings

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        await engine.dispose()
        pytest.skip("no reachable PostgreSQL instance")

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            yield session
    finally:
        await engine.dispose()
