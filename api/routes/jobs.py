from fastapi import APIRouter, HTTPException, status

from api.services.job_service import job_service
from shared.schemas import Job


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


@router.post(
    "",
    response_model=Job,
    status_code=status.HTTP_201_CREATED,
)
def create_job() -> Job:
    """
    Create a new UNTANGLE processing job.
    """
    return job_service.create_job()


@router.get(
    "/{job_id}/status",
    response_model=Job,
)
def get_job_status(job_id: str) -> Job:
    """
    Get the current status of a processing job.
    """
    job = job_service.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' was not found.",
        )

    return job