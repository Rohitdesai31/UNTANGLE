from __future__ import annotations

from threading import Lock
from uuid import uuid4

from shared.schemas import Job


class JobService:
    """
    In-memory job manager for the UNTANGLE API.

    This service is intentionally storage-independent.
    Later, the storage implementation can be replaced by
    a database or persistent job store without changing the API routes.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = Lock()

    def create_job(self) -> Job:
        job = Job(
            id=str(uuid4()),
            status="created",
            message="Job created successfully.",
        )

        with self._lock:
            self._jobs[job.id] = job

        return job

    def get_job(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update_status(
        self,
        job_id: str,
        status: str,
        message: str | None = None,
    ) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)

            if job is None:
                return None

            updated_job = Job(
                id=job.id,
                status=status,
                message=message,
            )

            self._jobs[job_id] = updated_job

            return updated_job


job_service = JobService()