from fastapi import FastAPI
from app.models.dtos.health_check import HealthCheck
from app.routers import lyrics_router
from app.configs.settings import settings
import uvicorn
from app.workers.audio_worker import process_audio_queue
from contextlib import asynccontextmanager
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = asyncio.create_task(process_audio_queue())
    print("Background Audio Queue Worker Started")

    yield

    worker_task.cancel()
    print("Background Audio Queue Worker Stopped")


app = FastAPI(title="WatESez", lifespan=lifespan)
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
        reload=True,
    )
