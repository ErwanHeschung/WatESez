from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities.lyrics import Lyrics
from typing import Optional


class LyricsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_fingerprint(self, fingerprint: str) -> Optional[Lyrics]:
        query = select(Lyrics).where(Lyrics.fingerprint == fingerprint)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def save(self, lyrics_obj: Lyrics) -> Lyrics:
        self.session.add(lyrics_obj)
        await self.session.commit()
        await self.session.refresh(lyrics_obj)
        return lyrics_obj

    async def get_by_id(self, lyrics_id: str) -> Optional[Lyrics]:
        return await self.session.get(Lyrics, lyrics_id)
