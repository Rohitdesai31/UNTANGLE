from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app


client = TestClient(app)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PID = ROOT / "samples" / "simple_pid.pdf"
SAMPLE_IO = ROOT / "samples" / "simple_io_list.xlsx"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["project"] == "UNTANGLE"


def test_create_job():
    response = client.post("/api/jobs")

    assert response.status_code == 201

    data = response.json()

    assert data["id"]
    assert data["status"] == "created"


def test_complete_fixture_pipeline():
    # 1. Create job
    response = client.post("/api/jobs")

    assert response.status_code == 201

    job = response.json()
    job_id = job["id"]

    # 2. Upload P&ID + IO list
    with (
        SAMPLE_PID.open("rb") as pid_file,
        SAMPLE_IO.open("rb") as io_file,
    ):
        response = client.post(
            f"/api/jobs/{job_id}/upload",
            files={
                "pid_file": (
                    "simple_pid.pdf",
                    pid_file,
                    "application/pdf",
                ),
                "io_file": (
                    "simple_io_list.xlsx",
                    io_file,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ),
            },
        )

    assert response.status_code in (200, 201)

    # 3. Process job
    response = client.post(
        f"/api/jobs/{job_id}/process"
    )

    assert response.status_code == 200

    process_data = response.json()

    assert process_data

    # 4. Check job status
    response = client.get(
        f"/api/jobs/{job_id}/status"
    )

    assert response.status_code == 200

    status_data = response.json()

    assert status_data["status"] == "completed"

    # 5. Get results
    response = client.get(
        f"/api/jobs/{job_id}/results"
    )

    assert response.status_code == 200

    results_data = response.json()

    assert results_data["job_id"] == job_id
    assert results_data["status"] == "completed"

    results = results_data["results"]

    assert results["graph"]
    assert results["graph_simple"]
    assert results["mapping"]
    assert results["audit"]
    assert results["sketch_path"]

    # 6. Check sketch
    response = client.get(
        f"/api/jobs/{job_id}/sketch"
    )

    assert response.status_code == 200
    assert "svg" in response.headers["content-type"]

    # 7. Check audit
    response = client.get(
        f"/api/jobs/{job_id}/audit"
    )

    assert response.status_code == 200

    # 8. Check graph
    response = client.get(
        f"/api/jobs/{job_id}/graph"
    )

    assert response.status_code == 200

    # 9. Check simplified graph
    response = client.get(
        f"/api/jobs/{job_id}/graph-simple"
    )

    assert response.status_code == 200

    # 10. Check mapping
    response = client.get(
        f"/api/jobs/{job_id}/mapping"
    )

    assert response.status_code == 200

    # 11. Check analysis
    response = client.get(
        f"/api/jobs/{job_id}/analysis"
    )

    assert response.status_code == 200

    analysis = response.json()

    assert analysis["job_id"] == job_id
    assert "symbols" in analysis
    assert "ocr" in analysis
    assert "lines" in analysis

    # 12. Check P&ID page
    response = client.get(
        f"/api/jobs/{job_id}/analysis/page/1"
    )

    assert response.status_code == 200

    page_data = response.json()

    assert page_data["page_number"] == 1
    assert page_data["page_count"] >= 1
    assert page_data["width"] > 0
    assert page_data["height"] > 0

    # 13. Check rendered P&ID page
    response = client.get(
        f"/api/jobs/{job_id}/analysis/page/1/image"
    )

    assert response.status_code == 200
    assert "image/png" in response.headers["content-type"]


def test_invalid_job_returns_404():
    job_id = "00000000-0000-0000-0000-000000000000"

    endpoints = [
        f"/api/jobs/{job_id}/status",
        f"/api/jobs/{job_id}/process",
        f"/api/jobs/{job_id}/results",
        f"/api/jobs/{job_id}/sketch",
        f"/api/jobs/{job_id}/pid",
        f"/api/jobs/{job_id}/audit",
        f"/api/jobs/{job_id}/graph",
        f"/api/jobs/{job_id}/graph-simple",
        f"/api/jobs/{job_id}/mapping",
        f"/api/jobs/{job_id}/analysis",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)

        if endpoint.endswith("/process"):
            response = client.post(endpoint)

        assert response.status_code == 404

def test_upload_invalid_file_types():
    client = TestClient(app)

    job_response = client.post("/api/jobs")
    assert job_response.status_code == 201

    job_id = job_response.json()["id"]

    response = client.post(
        f"/api/jobs/{job_id}/upload",
        files={
            "pid_file": (
                "drawing.txt",
                b"invalid",
                "text/plain",
            ),
            "io_file": (
                "io.txt",
                b"invalid",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 400
    assert "Invalid P&ID file type" in response.json()["detail"]


def test_upload_missing_files():
    client = TestClient(app)

    job_response = client.post("/api/jobs")
    assert job_response.status_code == 201

    job_id = job_response.json()["id"]

    response = client.post(
        f"/api/jobs/{job_id}/upload",
        files={},
    )

    assert response.status_code == 422


def test_analysis_invalid_page_number():
    client = TestClient(app)

    job_response = client.post("/api/jobs")
    assert job_response.status_code == 201

    job_id = job_response.json()["id"]

    response = client.get(
        f"/api/jobs/{job_id}/analysis/page/0"
    )

    assert response.status_code == 404 or response.status_code == 400


def test_results_for_unknown_job():
    client = TestClient(app)

    response = client.get(
        "/api/jobs/unknown-job-id/results"
    )

    assert response.status_code == 404

def test_add_and_get_correction():
    client = TestClient(app)

    job_response = client.post("/api/jobs")
    assert job_response.status_code == 201

    job_id = job_response.json()["id"]

    correction_response = client.post(
        f"/api/jobs/{job_id}/corrections",
        json={
            "original_id": "SYM-001",
            "field": "tag",
            "value": "P-101A",
        },
    )

    assert correction_response.status_code == 201

    correction_data = correction_response.json()

    assert correction_data["message"] == "Correction saved successfully."
    assert correction_data["correction"]["original_id"] == "SYM-001"
    assert correction_data["correction"]["field"] == "tag"
    assert correction_data["correction"]["value"] == "P-101A"

    get_response = client.get(
        f"/api/jobs/{job_id}/corrections"
    )

    assert get_response.status_code == 200

    corrections = get_response.json()["corrections"]

    assert len(corrections) == 1
    assert corrections[0]["original_id"] == "SYM-001"
    assert corrections[0]["value"] == "P-101A"


def test_correction_unknown_job_returns_404():
    client = TestClient(app)

    response = client.post(
        "/api/jobs/unknown-job-id/corrections",
        json={
            "original_id": "SYM-001",
            "field": "tag",
            "value": "P-101A",
        },
    )

    assert response.status_code == 404


def test_get_corrections_unknown_job_returns_404():
    client = TestClient(app)

    response = client.get(
        "/api/jobs/unknown-job-id/corrections"
    )

    assert response.status_code == 404