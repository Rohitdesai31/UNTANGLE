from pathlib import Path

import pytest

from api.routes import jobs
from api.services.job_service import job_service


def test_process_job_creates_error_artifact(
    monkeypatch,
    tmp_path,
):
    output_dir = tmp_path / "outputs"

    monkeypatch.setattr(
        jobs,
        "BASE_OUTPUT_DIR",
        output_dir,
    )

    def failing_process_job(job_id: str):
        raise ValueError("Synthetic pipeline failure")

    monkeypatch.setattr(
        jobs.pipeline_service,
        "process_job",
        failing_process_job,
    )

    job = job_service.create_job()

    with pytest.raises(Exception) as exc_info:
        jobs.process_job(job.id)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == (
        "UNTANGLE processing failed. Check the job error report."
    )

    error_path = output_dir / job.id / "error.json"

    assert error_path.exists()

    error_text = error_path.read_text(encoding="utf-8")

    assert '"job_id"' in error_text
    assert '"stage": "validation"' in error_text
    assert '"message": "Synthetic pipeline failure"' in error_text

    updated_job = job_service.get_job(job.id)

    assert updated_job is not None
    assert updated_job.status == "failed"
    assert updated_job.message == "UNTANGLE processing failed."