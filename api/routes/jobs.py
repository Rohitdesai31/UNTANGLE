from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from api.services.job_service import job_service
from api.services.pipeline_service import pipeline_service
from shared.schemas import Job


BASE_OUTPUT_DIR = Path("data/outputs")


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


def _write_error_artifact(
    job_id: str,
    stage: str,
    error_message: str,
) -> None:
    output_dir = BASE_OUTPUT_DIR / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    error_path = output_dir / "error.json"

    error_data = {
        "job_id": job_id,
        "stage": stage,
        "message": error_message,
    }

    with error_path.open("w", encoding="utf-8") as file:
        json.dump(error_data, file, indent=2)


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
        _write_error_artifact(
            job_id=job_id,
            stage="input",
            error_message=str(exc),
        )

        job_service.update_status(
            job_id,
            "failed",
            "UNTANGLE processing failed.",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="UNTANGLE processing failed. Check the job error report.",
        ) from exc

    except ValueError as exc:
        _write_error_artifact(
            job_id=job_id,
            stage="validation",
            error_message=str(exc),
        )

        job_service.update_status(
            job_id,
            "failed",
            "UNTANGLE processing failed.",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="UNTANGLE processing failed. Check the job error report.",
        ) from exc

    except Exception as exc:
        _write_error_artifact(
            job_id=job_id,
            stage="pipeline",
            error_message=str(exc),
        )

        job_service.update_status(
            job_id,
            "failed",
            "UNTANGLE processing failed.",
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="UNTANGLE processing failed. Check the job error report.",
        ) from exc