from __future__ import annotations

import json
from pathlib import Path

import pymupdf
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse


UPLOAD_DIR = Path("data/uploads")
INTERMEDIATE_DIR = Path("data/intermediate")


router = APIRouter(
    prefix="/jobs",
    tags=["analysis"],
)


def get_pid_path(job_id: str) -> Path:
    return UPLOAD_DIR / job_id / "pid.pdf"


def get_intermediate_dir(job_id: str) -> Path:
    return INTERMEDIATE_DIR / job_id


def load_json_if_exists(path: Path) -> list | dict:
    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


@router.get("/{job_id}/analysis")
def get_analysis(job_id: str) -> dict:
    pid_path = get_pid_path(job_id)

    if not pid_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"P&ID for job '{job_id}' was not found.",
        )

    intermediate_dir = get_intermediate_dir(job_id)

    symbols = load_json_if_exists(
        intermediate_dir / "symbols.json"
    )

    ocr = load_json_if_exists(
        intermediate_dir / "ocr.json"
    )

    lines = load_json_if_exists(
        intermediate_dir / "lines.json"
    )

    return {
        "job_id": job_id,
        "symbols": symbols,
        "ocr": ocr,
        "lines": lines,
    }


@router.get("/{job_id}/analysis/page/{page_number}")
def get_analysis_page(
    job_id: str,
    page_number: int,
) -> dict:

    pid_path = get_pid_path(job_id)

    if not pid_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"P&ID for job '{job_id}' was not found.",
        )

    if page_number < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must start from 1.",
        )

    document = None

    try:
        document = pymupdf.open(pid_path)

        page_count = len(document)

        if page_number > page_count:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Page {page_number} does not exist.",
            )

        page = document[page_number - 1]

        return {
            "job_id": job_id,
            "page_number": page_number,
            "page_count": page_count,
            "width": page.rect.width,
            "height": page.rect.height,
            "image_url": (
                f"/api/jobs/{job_id}/analysis/"
                f"page/{page_number}/image"
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to read P&ID page: {exc}",
        ) from exc

    finally:
        if document is not None:
            document.close()


@router.get("/{job_id}/analysis/page/{page_number}/image")
def get_analysis_page_image(
    job_id: str,
    page_number: int,
) -> FileResponse:

    pid_path = get_pid_path(job_id)

    if not pid_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"P&ID for job '{job_id}' was not found.",
        )

    if page_number < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must start from 1.",
        )

    output_dir = (
        INTERMEDIATE_DIR
        / job_id
        / "pages"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / f"page_{page_number}.png"
    )

    document = None

    try:
        document = pymupdf.open(pid_path)

        if page_number > len(document):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Page {page_number} does not exist.",
            )

        page = document[page_number - 1]

        if not output_path.exists():
            matrix = pymupdf.Matrix(2, 2)

            pixmap = page.get_pixmap(
                matrix=matrix,
                alpha=False,
            )

            pixmap.save(output_path)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to render P&ID page: {exc}",
        ) from exc

    finally:
        if document is not None:
            document.close()

    return FileResponse(
        path=output_path,
        media_type="image/png",
        filename=f"page_{page_number}.png",
        content_disposition_type="inline",
    )