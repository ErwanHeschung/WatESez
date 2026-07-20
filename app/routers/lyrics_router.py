import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, UploadFile, HTTPException, status

from app.dependencies import JobRepositoryDep, LyricsRepositoryDep
from app.configs.settings import settings
from app.models.dtos.error_response import ErrorResponse
from app.models.dtos.job import JobAccepted, JobStatusResponse
from app.workers.audio_worker import job_available

router = APIRouter(prefix="/lyrics", tags=["lyrics"])

JOB_STORAGE_DIR = Path("./storage/jobs")


@router.post(
    "/register",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobAccepted,
    responses={
        400: {"model": ErrorResponse, "description": "File must be an audio type"},
        429: {"model": ErrorResponse, "description": "Processing queue is full"},
        500: {"description": "Internal Server Error during processing"},
    },
)
async def upload_audio(file: UploadFile, job_repo: JobRepositoryDep):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Please upload an audio file.",
        )

    pending = await job_repo.count_pending()
    if pending >= settings.audio_queue_max_size:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Processing queue is full ({pending} pending). Retry later.",
        )

    filename = file.filename or "unknown file"

    JOB_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    audio_path = JOB_STORAGE_DIR / f"{uuid.uuid4()}{Path(filename).suffix}"

    async with aiofiles.open(audio_path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            await out.write(chunk)

    try:
        job = await job_repo.create(filename=filename, audio_path=str(audio_path))
    except Exception:
        audio_path.unlink(missing_ok=True)
        raise

    job_available.set()

    return JobAccepted(
        job_id=job.id,
        status=job.status,
        filename=job.filename,
        message=f"{filename} queued. Poll /lyrics/jobs/{job.id} for status.",
    )


@router.get(
    "/jobs/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=JobStatusResponse,
    responses={404: {"model": ErrorResponse, "description": "Job not found"}},
)
async def get_job(job_id: str, job_repo: JobRepositoryDep):
    job = await job_repo.get_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        filename=job.filename,
        fingerprint=job.fingerprint,
        error=job.error,
        attempts=job.attempts,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
    )


@router.get(
    "/{fingerprint}",
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Lyrics not found for the given fingerprint",
        },
        500: {"description": "Internal Server Error during retrieval"},
    },
)
async def get_lyrics(fingerprint: str, lyrics_repo: LyricsRepositoryDep):
    existing_lyrics = await lyrics_repo.get_by_fingerprint(fingerprint)

    if not existing_lyrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lyrics not found for the given fingerprint",
        )
    return existing_lyrics
