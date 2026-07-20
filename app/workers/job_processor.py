import asyncio
import logging
from pathlib import Path

from app.configs.database import async_session_maker
from app.models.entities.job import Job
from app.repositories.job_repository import JobRepository
from app.repositories.lyrics_repository import LyricsRepository
from app.services.audio_service import AudioService
from app.services.fingerprint_service import FingerprintService
from app.services.noise_remover_service import NoiseRemoverService
from app.services.stt_service import STTService

logger = logging.getLogger(__name__)


class JobProcessor:
    """Runs claimed jobs to completion and records the outcome.

    Separated from the worker loop, which now only decides *when* to look for
    work. The models are held on the instance because loading them is
    expensive and they are reused across every job.
    """

    def __init__(self):
        self.fingerprint_service = FingerprintService()
        self.noise_remover = NoiseRemoverService()
        self.stt = STTService()

    async def run_pending(self) -> bool:
        """Process pending jobs until none remain. Returns whether any ran."""
        processed_any = False

        while True:
            async with async_session_maker() as session:
                job_repo = JobRepository(session)
                job = await job_repo.claim_next()

                if job is None:
                    return processed_any

                processed_any = True
                await self._run_one(job, job_repo, session)

    async def _run_one(self, job: Job, job_repo: JobRepository, session) -> None:
        job_id, audio_path, filename = job.id, job.audio_path, job.filename

        try:
            audio_bytes = await asyncio.to_thread(Path(audio_path).read_bytes)

            audio_service = AudioService(
                fingerprint_service=self.fingerprint_service,
                noise_remover_service=self.noise_remover,
                stt_service=self.stt,
                lyrics_repo=LyricsRepository(session=session),
            )
            fingerprint = await audio_service.register_lyrics(audio_bytes, filename)

            await job_repo.mark_completed(job_id, fingerprint)
            logger.info("Job %s completed (%s)", job_id, filename)

        except asyncio.CancelledError:
            logger.info("Job %s interrupted by shutdown; will be requeued", job_id)
            raise

        except Exception as exc:
            logger.exception("Job %s failed (%s)", job_id, filename)
            await job_repo.mark_failed(job_id, f"{type(exc).__name__}: {exc}")
            Path(audio_path).unlink(missing_ok=True)

        else:
            Path(audio_path).unlink(missing_ok=True)
