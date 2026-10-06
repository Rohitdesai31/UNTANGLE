from fastapi import APIRouter, File, HTTPException, UploadFile, status

from api.services.job_service import job_service
from api.services.upload_service import upload_service


router = APIRouter(
    prefix="/jobs",
    tags=["upload"],
)


@router.post(
    "/{job_id}/upload",
    status_code=status.HTTP_201_CREATED,
)
async def upload_job_files(
    job_id: str,
    pid_file: UploadFile = File(...),
    io_file: UploadFile = File(...),
) -> dict:
    """
    Upload the P&ID PDF and IO List Excel file for a job.
    """

    job = job_service.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' was not found.",
        )

    try:
        files = await upload_service.save_job_files(
            job=job,
            pid_file=pid_file,
            io_file=io_file,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return {
        "message": "Files uploaded successfully.",
        "files": files,
    }