import asyncio
import logging
from pathlib import Path

from app.configs.database import async_session_maker
from app.services.noise_remover_service import NoiseRemoverService
from app.services.stt_service import STTService
from app.repositories.lyrics_repository import LyricsRepository
from app.repositories.job_repository import JobRepository
from app.services.audio_service import AudioService

logger = logging.getLogger(__name__)

job_available = asyncio.Event()

POLL_INTERVAL_SECONDS = 5


async def process_audio_queue():
    noise_remover = NoiseRemoverService()
    stt = STTService()

    async with async_session_maker() as db_session:
        recovered = await JobRepository(db_session).requeue_orphans()
    if recovered:
        logger.warning("Requeued %d job(s) interrupted by a previous shutdown", recovered)

    while True:
        job_available.clear()

        processed_any = await _drain(noise_remover, stt)

        if not processed_any:
            try:
                await asyncio.wait_for(
                    job_available.wait(), timeout=POLL_INTERVAL_SECONDS
                )
            except asyncio.TimeoutError:
                pass


async def _drain(noise_remover: NoiseRemoverService, stt: STTService) -> bool:
    """Process pending jobs until none remain. Returns whether any job ran."""
    processed_any = False

    while True:
        async with async_session_maker() as db_session:
            job_repo = JobRepository(db_session)
            job = await job_repo.claim_next()

            if job is None:
                return processed_any

            processed_any = True
            job_id, audio_path, filename = job.id, job.audio_path, job.filename

            try:
                audio_bytes = await asyncio.to_thread(Path(audio_path).read_bytes)

                audio_service = AudioService(
                    noise_remover_service=noise_remover,
                    stt_service=stt,
                    lyrics_repo=LyricsRepository(session=db_session),
                )
                fingerprint = await audio_service.register_lyrics(
                    audio_bytes, filename
                )

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
