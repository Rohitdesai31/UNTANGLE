from __future__ import annotations

import json
from pathlib import Path

from m1_vision.pdf_processor import pdf_to_images


BASE_UPLOAD_DIR = Path("data/uploads")
BASE_INTERMEDIATE_DIR = Path("data/intermediate")


class M1Service:
    """
    M4 integration boundary for the M1 Vision module.

    Current status:
    - Converts the uploaded P&ID PDF into page images.
    - Creates a job-specific intermediate directory.
    - Preserves the interface required by M2.
    - Does not invent vision/OCR/detection results.

    When the real M1 implementation is ready, its outputs can be
    written into this same job-specific intermediate directory.
    """

    def prepare_job(self, job_id: str) -> dict:
        upload_dir = BASE_UPLOAD_DIR / job_id
        intermediate_dir = BASE_INTERMEDIATE_DIR / job_id
        pages_dir = intermediate_dir / "pages"

        pid_path = upload_dir / "pid.pdf"
        io_path = upload_dir / "io_list.xlsx"

        if not pid_path.exists():
            raise FileNotFoundError(
                f"Uploaded P&ID not found: {pid_path}"
            )

        if not io_path.exists():
            raise FileNotFoundError(
                f"Uploaded IO list not found: {io_path}"
            )

        intermediate_dir.mkdir(parents=True, exist_ok=True)

        # Convert the uploaded PDF into page images.
        pdf_to_images(
            pdf_path=str(pid_path),
            output_dir=str(pages_dir),
        )

        page_images = sorted(
            str(path)
            for path in pages_dir.glob("page_*.png")
        )

        if not page_images:
            raise ValueError(
                f"No page images were generated from P&ID: {pid_path}"
            )

        metadata = {
            "job_id": job_id,
            "pid_file": str(pid_path),
            "io_file": str(io_path),
            "pages_dir": str(pages_dir),
            "page_images": page_images,
            "status": "prepared",
        }

        metadata_path = intermediate_dir / "m1_input.json"

        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)

        return metadata


m1_service = M1Service()