import uuid
from pathlib import Path
from typing import BinaryIO

import aiofiles

from app.configs.settings import settings
from app.exceptions import JobNotFoundError, QueueFullError
from app.models.entities.job import Job
from app.repositories.job_repository import JobRepository
from app.workers.signals import job_available

CHUNK_SIZE = 1024 * 1024


class JobService:
    """Owns the intake side of the queue: capacity, durable storage, tracking.

    The router previously did this inline, which mixed HTTP concerns with
    filesystem layout and queue policy.
    """

    def __init__(self, job_repo: JobRepository, storage_dir: Path | None = None):
        self.job_repo = job_repo
        self.storage_dir = storage_dir or Path(settings.job_storage_dir)

    async def enqueue(self, upload: BinaryIO, filename: str) -> Job:
        """Persist the upload and register it for processing.

        Raises QueueFullError rather than blocking; a bounded in-memory queue
        used to make the request hang until a slot freed.
        """
        pending = await self.job_repo.count_pending()
        if pending >= settings.audio_queue_max_size:
            raise QueueFullError(pending)

        audio_path = await self._store(upload, filename)

        try:
            job = await self.job_repo.create(
                filename=filename, audio_path=str(audio_path)
            )
        except Exception:
            audio_path.unlink(missing_ok=True)
            raise

        job_available.set()
        return job

    async def get_job(self, job_id: str) -> Job:
        job = await self.job_repo.get_by_id(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        return job

    async def _store(self, upload: BinaryIO, filename: str) -> Path:
        """Write the upload to disk before it is acknowledged, so that a
        restart cannot lose work a caller already received a 202 for."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        audio_path = self.storage_dir / f"{uuid.uuid4()}{Path(filename).suffix}"

        async with aiofiles.open(audio_path, "wb") as out:
            while chunk := await upload.read(CHUNK_SIZE):
                await out.write(chunk)

        return audio_path
