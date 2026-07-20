from typing import Annotated, TypeAlias

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.configs.database import get_db
from app.repositories.job_repository import JobRepository
from app.repositories.lyrics_repository import LyricsRepository
from app.services.job_service import JobService


def get_job_repository(db: AsyncSession = Depends(get_db)) -> JobRepository:
    return JobRepository(session=db)


def get_lyrics_repository(db: AsyncSession = Depends(get_db)) -> LyricsRepository:
    return LyricsRepository(session=db)


def get_job_service(
    job_repo: JobRepository = Depends(get_job_repository),
) -> JobService:
    return JobService(job_repo=job_repo)


def valid_audio_upload(file: UploadFile) -> UploadFile:
    """Reject non-audio uploads before the route body runs."""
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid file type: {file.content_type}. Please upload an audio file."
            ),
        )
    return file


JobRepositoryDep: TypeAlias = Annotated[JobRepository, Depends(get_job_repository)]
LyricsRepositoryDep: TypeAlias = Annotated[
    LyricsRepository, Depends(get_lyrics_repository)
]
JobServiceDep: TypeAlias = Annotated[JobService, Depends(get_job_service)]
AudioUploadDep: TypeAlias = Annotated[UploadFile, Depends(valid_audio_upload)]
