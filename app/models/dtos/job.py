from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class JobAccepted(BaseModel):
    job_id: str
    status: str
    filename: str
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    filename: str
    fingerprint: Optional[str] = None
    error: Optional[str] = None
    attempts: int
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
