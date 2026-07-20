from typing import Annotated, TypeAlias
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.database import get_db
from app.repositories.job_repository import JobRepository
from app.repositories.lyrics_repository import LyricsRepository


def get_job_repository(db: AsyncSession = Depends(get_db)) -> JobRepository:
    return JobRepository(session=db)


def get_lyrics_repository(db: AsyncSession = Depends(get_db)) -> LyricsRepository:
    return LyricsRepository(session=db)


JobRepositoryDep: TypeAlias = Annotated[JobRepository, Depends(get_job_repository)]
LyricsRepositoryDep: TypeAlias = Annotated[
    LyricsRepository, Depends(get_lyrics_repository)
]
