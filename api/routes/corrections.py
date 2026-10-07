from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from api.services.job_service import job_service


CORRECTIONS_DIR = Path("data/intermediate")

router = APIRouter(
    prefix="/jobs",
    tags=["corrections"],
)


class Correction(BaseModel):
    original_id: str
    field: str
    value: str


def get_corrections_path(job_id: str) -> Path:
    return CORRECTIONS_DIR / job_id / "corrections.json"


def load_corrections(job_id: str) -> list[dict]:
    path = get_corrections_path(job_id)

    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    return data if isinstance(data, list) else []


def save_corrections(
    job_id: str,
    corrections: list[dict],
) -> None:
    path = get_corrections_path(job_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(
            corrections,
            file,
            indent=2,
            ensure_ascii=False,
        )


@router.get("/{job_id}/corrections")
def get_corrections(job_id: str) -> dict:
    job = job_service.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' was not found.",
        )

    return {
        "job_id": job_id,
        "corrections": load_corrections(job_id),
    }


@router.post(
    "/{job_id}/corrections",
    status_code=status.HTTP_201_CREATED,
)
def add_correction(
    job_id: str,
    correction: Correction,
) -> dict:
    job = job_service.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' was not found.",
        )

    if not correction.original_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="original_id is required.",
        )

    if not correction.field.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="field is required.",
        )

    corrections = load_corrections(job_id)

    correction_data = correction.model_dump()

    corrections.append(correction_data)

    save_corrections(
        job_id,
        corrections,
    )

    return {
        "message": "Correction saved successfully.",
        "job_id": job_id,
        "correction": correction_data,
    }