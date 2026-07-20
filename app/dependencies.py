from typing import Annotated, TypeAlias
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.database import get_db
from app.services.audio_service import AudioService, get_audio_service
from app.repositories.job_repository import JobRepository

AudioServiceDep: TypeAlias = Annotated[AudioService, Depends(get_audio_service)]


def get_job_repository(db: AsyncSession = Depends(get_db)) -> JobRepository:
    return JobRepository(session=db)


JobRepositoryDep: TypeAlias = Annotated[JobRepository, Depends(get_job_repository)]
