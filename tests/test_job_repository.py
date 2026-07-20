"""Durability tests: the queue lives in the database so a restart cannot drop
work that has already been acknowledged with a 202."""

import asyncio

import pytest
from sqlalchemy import text

from app.models.entities.job import JobStatus
from app.repositories.job_repository import JobRepository

pytestmark = pytest.mark.integration


@pytest.fixture
async def repo(db_session):
    await db_session.execute(text("DELETE FROM jobs"))
    await db_session.commit()
    return JobRepository(db_session)


async def test_created_jobs_start_pending(repo):
    job = await repo.create("a.mp3", "/tmp/a.mp3")

    assert job.status == JobStatus.PENDING.value
    assert job.attempts == 0
    assert await repo.count_pending() == 1


async def test_claims_the_oldest_job_first(repo):
    first = await repo.create("a.mp3", "/tmp/a.mp3")
    await asyncio.sleep(0.01)
    second = await repo.create("b.mp3", "/tmp/b.mp3")

    assert (await repo.claim_next()).id == first.id
    assert (await repo.claim_next()).id == second.id


async def test_claiming_marks_the_job_in_flight(repo):
    await repo.create("a.mp3", "/tmp/a.mp3")

    claimed = await repo.claim_next()

    assert claimed.status == JobStatus.PROCESSING.value
    assert claimed.attempts == 1
    assert claimed.started_at is not None
    assert await repo.count_pending() == 0


async def test_claiming_an_empty_queue_returns_none(repo):
    assert await repo.claim_next() is None


async def test_completion_records_the_fingerprint(repo, db_session):
    job = await repo.create("a.mp3", "/tmp/a.mp3")
    await repo.claim_next()

    await repo.mark_completed(job.id, "fp_abc")

    done = await repo.get_by_id(job.id)
    await db_session.refresh(done)
    assert done.status == JobStatus.COMPLETED.value
    assert done.fingerprint == "fp_abc"
    assert done.finished_at is not None


async def test_failure_is_recorded_rather_than_swallowed(repo, db_session):
    job = await repo.create("a.mp3", "/tmp/a.mp3")
    await repo.claim_next()

    await repo.mark_failed(job.id, "boom")

    failed = await repo.get_by_id(job.id)
    await db_session.refresh(failed)
    assert failed.status == JobStatus.FAILED.value
    assert "boom" in failed.error


async def test_long_errors_are_truncated(repo, db_session):
    job = await repo.create("a.mp3", "/tmp/a.mp3")
    await repo.claim_next()

    await repo.mark_failed(job.id, "X" * 5000)

    failed = await repo.get_by_id(job.id)
    await db_session.refresh(failed)
    assert len(failed.error) == 2000


async def test_a_job_interrupted_by_a_crash_is_requeued(repo, db_session):
    job = await repo.create("a.mp3", "/tmp/a.mp3")
    await repo.claim_next()  # left PROCESSING, as a killed worker would

    assert await repo.requeue_orphans() == 1

    recovered = await repo.get_by_id(job.id)
    await db_session.refresh(recovered)
    assert recovered.status == JobStatus.PENDING.value
    assert recovered.started_at is None
    assert recovered.attempts == 1, "attempt history must survive recovery"


async def test_requeue_leaves_finished_jobs_alone(repo, db_session):
    job = await repo.create("a.mp3", "/tmp/a.mp3")
    await repo.claim_next()
    await repo.mark_completed(job.id, "fp")

    assert await repo.requeue_orphans() == 0

    done = await repo.get_by_id(job.id)
    await db_session.refresh(done)
    assert done.status == JobStatus.COMPLETED.value
