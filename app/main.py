from fastapi import FastAPI
from app.models.health_check import HealthCheck
from app.routers import lyrics

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