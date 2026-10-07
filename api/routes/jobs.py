from fastapi import APIRouter, HTTPException, status

from api.services.job_service import job_service
from api.services.pipeline_service import pipeline_service
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
@router.post(
    "/{job_id}/process",
)
def process_job(job_id: str) -> dict:
    job = job_service.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' was not found.",
        )

    job_service.update_status(
        job_id,
        "processing",
        "UNTANGLE processing started.",
    )

    try:
        result = pipeline_service.process_job(job_id)

        job_service.update_status(
            job_id,
            "completed",
            "UNTANGLE processing completed successfully.",
        )

        return result

    except FileNotFoundError as exc:
        job_service.update_status(
            job_id,
            "failed",
            str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        job_service.update_status(
            job_id,
            "failed",
            str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="UNTANGLE processing failed.",
        ) from exc

     