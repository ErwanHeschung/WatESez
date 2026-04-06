from fastapi import FastAPI
from app.models.health_check import HealthCheck
from app.routers import lyrics
from app.configs.settings import settings
import uvicorn

app = FastAPI(title="WatESez")
app.include_router(lyrics.router)

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
        reload=True
    )