import uuid
from enum import StrEnum
from sqlalchemy import Column, String, Text, Integer, DateTime, func
from app.models.entities.base import Base


class JobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    status = Column(
        String(16), nullable=False, index=True, default=JobStatus.PENDING.value
    )
    filename = Column(String, nullable=False)

    audio_path = Column(String, nullable=False)

    fingerprint = Column(String, nullable=True, index=True)
    error = Column(Text, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
