import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.configs.settings import settings
from app.exception_handlers import register_exception_handlers
from app.models.dtos.health_check import HealthCheck
from app.routers import jobs_router, lyrics_router
from app.workers.audio_worker import process_audio_queue

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = asyncio.create_task(process_audio_queue())
    logger.info("Background audio worker started")

    yield

    worker_task.cancel()

    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    logger.info("Background audio worker stopped")


app = FastAPI(title="WatESez", lifespan=lifespan)

register_exception_handlers(app)

# Order matters: jobs_router owns /lyrics/register and /lyrics/jobs/{job_id},
# which would otherwise be captured by the /lyrics/{fingerprint} route.
app.include_router(jobs_router.router)
app.include_router(lyrics_router.router)


@app.get(
    "/health",
    tags=["healthcheck"],
    summary="Perform a Health Check",
    response_description="Return HTTP 200 if the service is healthy.",
    response_model=HealthCheck,
)
async def get_health():
    return HealthCheck(status="OK")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.service_host,
        port=settings.service_port,
    )
