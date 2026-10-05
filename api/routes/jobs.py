from fastapi import APIRouter
router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("")
def create_job():
    return {"message": "job endpoint ready"}

@router.get("/{job_id}/status")
def job_status(job_id: str):
    return {"job_id": job_id, "status": "created"}
