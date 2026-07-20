import sys
import types

import pytest

# libchromaprint is a native dependency that is not present in every dev
# environment. app.services.fingerprint_service imports chromaprint at module
# scope, so stub it before any app import to keep the other tests runnable.
try:  # pragma: no cover - depends on the host
    import chromaprint  # noqa: F401
except Exception:  # pragma: no cover
    sys.modules["chromaprint"] = types.ModuleType("chromaprint")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_engine():
    """A NullPool engine scoped to one test.

    pytest-asyncio runs each test on its own event loop and a pooled asyncpg
    connection cannot cross loops, so the application's module-level engine is
    unusable here. Skips when no database is reachable.
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    from app.configs.settings import settings

    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        await engine.dispose()
        pytest.skip("no reachable PostgreSQL instance")

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture
async def db_session(db_engine):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
