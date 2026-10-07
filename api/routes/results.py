from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
 

BASE_OUTPUT_DIR = Path("data/outputs")


router = APIRouter(
    prefix="/jobs",
    tags=["results"],
)


@router.get("/{job_id}/results")
def get_job_results(job_id: str) -> dict:
    """
    Return generated results for a completed UNTANGLE job.
    """
    output_dir = BASE_OUTPUT_DIR / job_id

    if not output_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Results for job '{job_id}' were not found.",
        )

    required_files = [
        "graph.json",
        "graph_simple.json",
        "mapping.json",
        "audit.json",
        "sketch.svg",
    ]

    missing_files = [
        filename
        for filename in required_files
        if not (output_dir / filename).exists()
    ]

    if missing_files:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Job results are incomplete.",
                "missing_files": missing_files,
            },
        )

    with (output_dir / "graph.json").open(
        "r",
        encoding="utf-8",
    ) as file:
        graph = json.load(file)

    with (output_dir / "graph_simple.json").open(
        "r",
        encoding="utf-8",
    ) as file:
        graph_simple = json.load(file)

    with (output_dir / "mapping.json").open(
        "r",
        encoding="utf-8",
    ) as file:
        mapping = json.load(file)

    with (output_dir / "audit.json").open(
        "r",
        encoding="utf-8",
    ) as file:
        audit = json.load(file)

    return {
        "job_id": job_id,
        "status": "completed",
        "results": {
            "graph": graph,
            "graph_simple": graph_simple,
            "mapping": mapping,
            "audit": audit,
            "sketch_path": str(output_dir / "sketch.svg"),
        },
    }


@router.get("/{job_id}/sketch")
def get_job_sketch(job_id: str) -> FileResponse:
    """
    Return the generated simplified process sketch as an SVG file.
    """
    sketch_path = BASE_OUTPUT_DIR / job_id / "sketch.svg"

    if not sketch_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sketch for job '{job_id}' was not found.",
        )

    return FileResponse(
        path=sketch_path,
        media_type="image/svg+xml",
        filename="sketch.svg",
        content_disposition_type="inline",
    )

@router.get("/{job_id}/pid")
def get_job_pid(job_id: str) -> FileResponse:
    pid_path = (
        Path("data/uploads")
        / job_id
        / "pid.pdf"
    )

    if not pid_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"P&ID for job '{job_id}' was not found.",
        )
    
    return FileResponse(
        path=pid_path,
        media_type="application/pdf",
        filename="pid.pdf",
        content_disposition_type="inline",
    )


@router.get("/{job_id}/audit")
def get_job_audit(job_id: str) -> FileResponse:
    """
    Download the audit report for a completed job.
    """
    audit_path = BASE_OUTPUT_DIR / job_id / "audit.json"

    if not audit_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit report for job '{job_id}' was not found.",
        )

    return FileResponse(
        path=audit_path,
        media_type="application/json",
        filename="audit.json",
        content_disposition_type="attachment",
    )


@router.get("/{job_id}/graph")
def get_job_graph(job_id: str) -> FileResponse:
    """
    Download the original process graph.
    """
    graph_path = BASE_OUTPUT_DIR / job_id / "graph.json"

    if not graph_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Graph for job '{job_id}' was not found.",
        )

    return FileResponse(
        path=graph_path,
        media_type="application/json",
        filename="graph.json",
        content_disposition_type="attachment",
    )


@router.get("/{job_id}/graph-simple")
def get_job_simple_graph(job_id: str) -> FileResponse:
    """
    Download the simplified process graph.
    """
    graph_path = BASE_OUTPUT_DIR / job_id / "graph_simple.json"

    if not graph_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simplified graph for job '{job_id}' was not found.",
        )

    return FileResponse(
        path=graph_path,
        media_type="application/json",
        filename="graph_simple.json",
        content_disposition_type="attachment",
    )


@router.get("/{job_id}/mapping")
def get_job_mapping(job_id: str) -> FileResponse:
    """
    Download original-to-simplified element mappings.
    """
    mapping_path = BASE_OUTPUT_DIR / job_id / "mapping.json"

    if not mapping_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping for job '{job_id}' was not found.",
        )

    return FileResponse(
        path=mapping_path,
        media_type="application/json",
        filename="mapping.json",
        content_disposition_type="attachment",
    )

   