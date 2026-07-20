import asyncio
import logging

from app.configs.database import async_session_maker
from app.repositories.job_repository import JobRepository
from app.workers.job_processor import JobProcessor
from app.workers.signals import job_available

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 5


async def process_audio_queue():
    """Decides when to look for work; JobProcessor decides what to do with it."""
    processor = JobProcessor()

    await _recover_interrupted_jobs()

    while True:
        job_available.clear()

        if not await processor.run_pending():
            await _wait_for_work()


async def _recover_interrupted_jobs() -> None:
    async with async_session_maker() as session:
        recovered = await JobRepository(session).requeue_orphans()

    if recovered:
        logger.warning(
            "Requeued %d job(s) interrupted by a previous shutdown", recovered
        )


async def _wait_for_work() -> None:
    """Wake early when the API signals, otherwise poll.

    The poll matters on startup: jobs left by a previous process have no
    pending signal to deliver.
    """
    try:
        await asyncio.wait_for(job_available.wait(), timeout=POLL_INTERVAL_SECONDS)
    except asyncio.TimeoutError:
        pass
