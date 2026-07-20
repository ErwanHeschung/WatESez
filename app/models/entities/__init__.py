"""Entity imports so Base.metadata is fully populated for Alembic autogenerate.

Without these, migrations/env.py sees an empty metadata and autogenerate emits
DROP statements for every existing table.
"""

from app.models.entities.base import Base
from app.models.entities.lyrics import Lyrics
from app.models.entities.job import Job, JobStatus

__all__ = ["Base", "Lyrics", "Job", "JobStatus"]
