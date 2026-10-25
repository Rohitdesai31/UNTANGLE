
from m2_topology.topology_validator import validate_topology


def test_valid_graph():
    graph = {
        "nodes": [
            {"id": "A", "type": "pump", "tag": "P-101"},
            {"id": "B", "type": "tank", "tag": "TK-101"},
        ],
        "edges": [{"id": "E1", "source": "A", "target": "B"}],
        "metadata": {},
    }

    result = validate_topology(graph)

    assert result["valid"] is True
    assert result["errors"] == []


def test_missing_target_node():
    graph = {
        "nodes": [{"id": "A", "type": "pump", "tag": "P-101"}],
        "edges": [{"id": "E1", "source": "A", "target": "MISSING"}],
        "metadata": {},
    }

    result = validate_topology(graph)

    assert result["valid"] is False
    assert any(
        error["reason"] == "target_node_missing"
        for error in result["invalid_connections"]
    )


def test_self_connection():
    graph = {
        "nodes": [{"id": "A", "type": "pump", "tag": "P-101"}],
        "edges": [{"id": "E1", "source": "A", "target": "A"}],
        "metadata": {},
    }

    result = validate_topology(graph)

    assert result["valid"] is False
    assert any(
        error["reason"] == "self_connection"
        for error in result["invalid_connections"]
    )


def test_unresolved_process_line():
    graph = {
        "nodes": [],
        "edges": [],
        "metadata": {"unresolved_process_lines": ["L-101"]},
    }

    result = validate_topology(graph)

    assert result["valid"] is False
    assert result["unresolved_process_lines"] == [
        {
            "line_id": "L-101",
            "reason": "unresolved_process_connection",
        }
    ]


def test_flow_direction_conflict():
    graph = {
        "nodes": [
            {"id": "A", "type": "pump"},
            {"id": "B", "type": "tank"},
        ],
        "edges": [{
            "id": "E1",
            "source": "A",
            "target": "B",
            "upstream": "B",
            "downstream": "A",
        }],
        "metadata": {},
    }

    result = validate_topology(graph)

    assert result["valid"] is False
    assert any(
        error["reason"] == "flow_direction_conflict"
        for error in result["flow_errors"]
    )


def test_duplicate_tags_are_reported_as_warning():
    graph = {
        "nodes": [
            {"id": "A", "type": "pump", "tag": "P-101"},
            {"id": "B", "type": "pump", "tag": "P-101"},
        ],
        "edges": [{"id": "E1", "source": "A", "target": "B"}],
        "metadata": {},
    }

    result = validate_topology(graph)

    assert "P-101" in result["duplicate_tags"]
    assert result["valid"] is True


def test_missing_expected_tag_is_reported():
    graph = {
        "nodes": [{"id": "A", "type": "pump", "tag": "P-101"}],
        "edges": [],
        "expected_tags": ["P-101", "FT-999"],
        "metadata": {},
    }

    result = validate_topology(graph)

    assert "FT-999" in result["missing_equipment"]
    assert result["valid"] is True


def test_duplicate_node_ids_are_detected():
    graph = {
        "nodes": [
            {"id": "A", "type": "pump"},
            {"id": "A", "type": "tank"},
        ],
        "edges": [],
        "metadata": {},
    }

    result = validate_topology(graph)

    assert result["valid"] is False
    assert any(
        error["reason"] == "duplicate_node_id"
        for error in result["consistency_errors"]
    )
