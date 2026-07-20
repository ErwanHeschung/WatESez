from fastapi import APIRouter, status

from app.dependencies import AudioUploadDep, JobServiceDep
from app.models.dtos.error_response import ErrorResponse
from app.models.dtos.job import JobAccepted, JobStatusResponse

router = APIRouter(prefix="/lyrics", tags=["jobs"])


@router.post(
    "/register",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=JobAccepted,
    responses={
        400: {"model": ErrorResponse, "description": "File must be an audio type"},
        429: {"model": ErrorResponse, "description": "Processing queue is full"},
    },
)
async def register_audio(file: AudioUploadDep, job_service: JobServiceDep):
    """Accept an upload for transcription.

    Returns immediately; poll the job endpoint for the outcome.
    """
    job = await job_service.enqueue(file, file.filename or "unknown file")

    return JobAccepted(
        job_id=job.id,
        status=job.status,
        filename=job.filename,
        message=f"Queued. Poll /lyrics/jobs/{job.id} for status.",
    )


@router.get(
    "/jobs/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=JobStatusResponse,
    responses={404: {"model": ErrorResponse, "description": "Job not found"}},
)
async def get_job(job_id: str, job_service: JobServiceDep):
    job = await job_service.get_job(job_id)

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
