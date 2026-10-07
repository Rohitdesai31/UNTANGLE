from m2_topology.topology_validator import (
    validate_topology,
)


def test_valid_process_graph():
    graph = {
        "nodes": [
            {"id": "T1", "tag": "TK-101", "type": "tank"},
            {"id": "P1", "tag": "P-101", "type": "pump"},
            {"id": "R1", "tag": "R-101", "type": "reactor"},
        ],
        "edges": [
            {
                "id": "E1",
                "source": "T1",
                "target": "P1",
                "upstream": "T1",
                "downstream": "P1",
            },
            {
                "id": "E2",
                "source": "P1",
                "target": "R1",
                "upstream": "P1",
                "downstream": "R1",
            },
        ],
    }

    result = validate_topology(graph)

    assert result["valid"] is True
    assert result["invalid_connections"] == []
    assert result["flow_errors"] == []
    assert result["disconnected_nodes"] == []


def test_disconnected_equipment():
    graph = {
        "nodes": [
            {"id": "T1", "tag": "TK-101", "type": "tank"},
            {"id": "P1", "tag": "P-101", "type": "pump"},
            {"id": "R1", "tag": "R-101", "type": "reactor"},
        ],
        "edges": [
            {
                "id": "E1",
                "source": "T1",
                "target": "P1",
            }
        ],
    }

    result = validate_topology(graph)

    assert "R1" in [
        item["id"]
        for item in result["disconnected_nodes"]
    ]


def test_invalid_connection():
    graph = {
        "nodes": [
            {"id": "T1", "tag": "TK-101", "type": "tank"},
        ],
        "edges": [
            {
                "id": "E1",
                "source": "T1",
                "target": "UNKNOWN",
            }
        ],
    }

    result = validate_topology(graph)

    assert result["valid"] is False
    assert any(
        item["reason"] == "target_node_missing"
        for item in result["invalid_connections"]
    )


def test_impossible_flow():
    graph = {
        "nodes": [
            {"id": "T1", "tag": "TK-101", "type": "tank"},
            {"id": "P1", "tag": "P-101", "type": "pump"},
        ],
        "edges": [
            {
                "id": "E1",
                "source": "T1",
                "target": "P1",
                "upstream": "P1",
                "downstream": "T1",
            }
        ],
    }

    result = validate_topology(graph)

    assert result["valid"] is False
    assert any(
        item["reason"] == "flow_direction_conflict"
        for item in result["flow_errors"]
    )


def test_branch_detection():
    graph = {
        "nodes": [
            {"id": "T1", "tag": "TK-101", "type": "tank"},
            {"id": "P1", "tag": "P-101", "type": "pump"},
            {"id": "R1", "tag": "R-101", "type": "reactor"},
            {"id": "R2", "tag": "R-102", "type": "reactor"},
        ],
        "edges": [
            {"source": "T1", "target": "P1"},
            {"source": "P1", "target": "R1"},
            {"source": "P1", "target": "R2"},
        ],
    }

    result = validate_topology(graph)

    assert len(result["branches"]) == 1
    assert result["branches"][0]["node_id"] == "P1"


def test_merge_detection():
    graph = {
        "nodes": [
            {"id": "P1", "tag": "P-101", "type": "pump"},
            {"id": "P2", "tag": "P-102", "type": "pump"},
            {"id": "R1", "tag": "R-101", "type": "reactor"},
        ],
        "edges": [
            {"source": "P1", "target": "R1"},
            {"source": "P2", "target": "R1"},
        ],
    }

    result = validate_topology(graph)

    assert len(result["merges"]) == 1
    assert result["merges"][0]["node_id"] == "R1"


def test_duplicate_tags():
    graph = {
        "nodes": [
            {"id": "P1", "tag": "P-101", "type": "pump"},
            {"id": "P2", "tag": "P-101", "type": "pump"},
        ],
        "edges": [],
    }

    result = validate_topology(graph)

    assert "P-101" in result["duplicate_tags"]
    assert result["duplicate_tags"]["P-101"] == [
        "P1",
        "P2",
    ]


def test_missing_equipment():
    graph = {
        "metadata": {
            "expected_tags": [
                "TK-101",
                "P-101",
                "R-101",
            ]
        },
        "nodes": [
            {"id": "T1", "tag": "TK-101", "type": "tank"},
            {"id": "P1", "tag": "P-101", "type": "pump"},
        ],
        "edges": [],
    }

    result = validate_topology(graph)

    assert result["missing_equipment"] == ["R-101"]