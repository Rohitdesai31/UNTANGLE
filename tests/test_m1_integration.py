from __future__ import annotations

import json

from api.services.m1_contract_service import m1_contract_service
from api.services.pipeline_service import pipeline_service


def test_real_m1_outputs_flow_into_m2_and_m3(tmp_path, monkeypatch):
    job_id = "test-real-m1-integration"

    intermediate_dir = tmp_path / "intermediate" / job_id
    output_dir = tmp_path / "outputs" / job_id

    intermediate_dir.mkdir(parents=True)

    symbols = [
        {
            "id": "M1-001",
            "class_name": "tank",
            "tag": "TK-101",
            "bbox": [100, 100, 180, 180],
            "confidence": 0.99,
            "page": 1,
        },
        {
            "id": "M1-002",
            "class_name": "pump",
            "tag": "P-101",
            "bbox": [250, 100, 330, 180],
            "confidence": 0.98,
            "page": 1,
        },
        {
            "id": "M1-003",
            "class_name": "outlet",
            "tag": "OUTLET",
            "bbox": [500, 100, 580, 180],
            "confidence": 0.99,
            "page": 1,
        },
    ]

    lines = [
        {
            "id": "M1-L001",
            "points": [[180, 140], [250, 140]],
            "line_type": "process",
            "confidence": 0.98,
            "page": 1,
        },
        {
            "id": "M1-L002",
            "points": [[330, 140], [500, 140]],
            "line_type": "process",
            "confidence": 0.98,
            "page": 1,
        },
    ]

    associations = [
        {
            "source_id": "M1-L001",
            "target_id": "M1-001",
            "relation": "connects_from",
            "confidence": 0.98,
        },
        {
            "source_id": "M1-L001",
            "target_id": "M1-002",
            "relation": "connects_to",
            "confidence": 0.98,
        },
        {
            "source_id": "M1-L002",
            "target_id": "M1-002",
            "relation": "connects_from",
            "confidence": 0.98,
        },
        {
            "source_id": "M1-L002",
            "target_id": "M1-003",
            "relation": "connects_to",
            "confidence": 0.98,
        },
    ]

    io_list = [
        {
            "tag": "FT-101",
            "type": "flow_transmitter",
            "description": "Flow transmitter",
            "loop": "101",
            "expected_status": "active",
        }
    ]

    files = {
        "symbols.json": symbols,
        "lines.json": lines,
        "associations.json": associations,
        "io_list.json": io_list,
    }

    for filename, data in files.items():
        with (intermediate_dir / filename).open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    monkeypatch.setattr(
        "api.services.m1_output_service.BASE_INTERMEDIATE_DIR",
        tmp_path / "intermediate",
    )

    monkeypatch.setattr(
        "api.services.m1_contract_service.BASE_INTERMEDIATE_DIR",
        tmp_path / "intermediate",
    )

    monkeypatch.setattr(
        "api.services.pipeline_service.BASE_INTERMEDIATE_DIR",
        tmp_path / "intermediate",
    )

    monkeypatch.setattr(
        "api.services.pipeline_service.BASE_OUTPUT_DIR",
        tmp_path / "outputs",
    )

    monkeypatch.setattr(
        "api.services.pipeline_service.BASE_UPLOAD_DIR",
        tmp_path / "uploads",
    )

    monkeypatch.setattr(
        "api.services.pipeline_service.FIXTURE_DIR",
        tmp_path / "fixtures",
    )

    contract = m1_contract_service.validate_job_outputs(job_id)

    assert contract["ready"] is True
    assert contract["counts"]["symbols"] == 3
    assert contract["counts"]["lines"] == 2
    assert contract["counts"]["associations"] == 4
    assert contract["counts"]["io_list"] == 1

    result = pipeline_service.process_job(job_id)

    assert result["status"] == "completed"
    assert result["summary"]["graph_nodes"] == 3
    assert result["summary"]["graph_edges"] == 2
    assert result["summary"]["simplified_nodes"] == 3
    assert result["summary"]["simplified_edges"] == 2
    assert result["summary"]["status"] == "PASS"

    assert output_dir.exists()
    assert (output_dir / "graph.json").exists()
    assert (output_dir / "graph_simple.json").exists()
    assert (output_dir / "mapping.json").exists()
    assert (output_dir / "sketch.svg").exists()
    assert (output_dir / "audit.json").exists()
