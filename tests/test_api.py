"""HTTP surface: routing, validation, and the domain-exception handlers."""

import io

import httpx
import pytest
from sqlalchemy import text

from app.main import app

pytestmark = pytest.mark.integration


def audio_file(name="song.mp3", data=b"FAKEAUDIO", content_type="audio/mpeg"):
    return {"file": (name, io.BytesIO(data), content_type)}


@pytest.fixture
async def client(db_engine, db_session, monkeypatch, tmp_path):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.configs.database import get_db

    await db_session.execute(text("DELETE FROM jobs"))
    await db_session.commit()

    monkeypatch.setattr(
        "app.services.job_service.settings.job_storage_dir", str(tmp_path)
    )

    session_maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.clear()


async def test_register_returns_a_job_id(client):
    response = await client.post("/lyrics/register", files=audio_file())

    assert response.status_code == 202
    body = response.json()
    assert body["job_id"]
    assert body["status"] == "pending"


async def test_job_route_is_not_captured_by_the_fingerprint_route(client):
    """/lyrics/jobs/{id} and /lyrics/{fingerprint} live in different routers
    now, so inclusion order is what keeps them apart."""
    registered = await client.post("/lyrics/register", files=audio_file())
    job_id = registered.json()["job_id"]

    response = await client.get(f"/lyrics/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json()["job_id"] == job_id
    assert response.json()["filename"] == "song.mp3"


async def test_unknown_job_is_a_404(client):
    response = await client.get("/lyrics/jobs/does-not-exist")

    assert response.status_code == 404
    assert "detail" in response.json()


async def test_unknown_fingerprint_is_a_404(client):
    assert (await client.get("/lyrics/no-such-fingerprint")).status_code == 404


async def test_non_audio_upload_is_rejected(client):
    response = await client.post(
        "/lyrics/register", files=audio_file("x.txt", b"x", "text/plain")
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


async def test_a_full_queue_is_rejected_rather_than_blocking(client, monkeypatch):
    monkeypatch.setattr("app.services.job_service.settings.audio_queue_max_size", 1)

    await client.post("/lyrics/register", files=audio_file("a.mp3"))
    response = await client.post("/lyrics/register", files=audio_file("b.mp3"))

    assert response.status_code == 429
    assert "queue is full" in response.json()["detail"].lower()


async def test_health_is_served(client):
    assert (await client.get("/health")).status_code == 200
