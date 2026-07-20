from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.configs.settings import settings

engine = create_async_engine(settings.database_url, echo=settings.db_echo)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with async_session_maker() as session:
        yield session
