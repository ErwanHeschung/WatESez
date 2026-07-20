from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities.job import Job, JobStatus


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, filename: str, audio_path: str) -> Job:
        job = Job(
            filename=filename,
            audio_path=audio_path,
            status=JobStatus.PENDING.value,
        )
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_by_id(self, job_id: str) -> Optional[Job]:
        return await self.session.get(Job, job_id)

    async def count_pending(self) -> int:
        query = select(func.count()).where(Job.status == JobStatus.PENDING.value)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def claim_next(self) -> Optional[Job]:
        """Atomically take the oldest pending job.

        SKIP LOCKED keeps this correct if a second worker is ever added; with
        the current single worker it is simply a no-op.
        """
        candidate = (
            select(Job.id)
            .where(Job.status == JobStatus.PENDING.value)
            .order_by(Job.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
            .scalar_subquery()
        )

        query = (
            update(Job)
            .where(Job.id == candidate)
            .values(
                status=JobStatus.PROCESSING.value,
                started_at=_now(),
                attempts=Job.attempts + 1,
            )
            .returning(Job)
        )
        result = await self.session.execute(query)
        job = result.scalar_one_or_none()
        await self.session.commit()
        return job

    async def mark_completed(self, job_id: str, fingerprint: str) -> None:
        await self._finish(
            job_id, JobStatus.COMPLETED, fingerprint=fingerprint, error=None
        )

    async def mark_failed(self, job_id: str, error: str) -> None:
        # Truncate: tracebacks can be long and this column is read by clients.
        await self._finish(job_id, JobStatus.FAILED, error=error[:2000])

    async def _finish(
        self,
        job_id: str,
        status: JobStatus,
        fingerprint: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        values = {
            "status": status.value,
            "finished_at": _now(),
            "error": error,
        }
        if fingerprint is not None:
            values["fingerprint"] = fingerprint

        await self.session.execute(update(Job).where(Job.id == job_id).values(**values))
        await self.session.commit()

    async def requeue_orphans(self) -> int:
        """Reset jobs left mid-flight by a crash or shutdown back to pending."""
        result = await self.session.execute(
            update(Job)
            .where(Job.status == JobStatus.PROCESSING.value)
            .values(status=JobStatus.PENDING.value, started_at=None)
        )
        await self.session.commit()
        return result.rowcount or 0
