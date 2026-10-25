
import pytest

from m2_topology.graph_builder import build_edges


def test_valid_process_line_creates_edge():
    """A valid source and target should create one edge."""

    lines = [
        {
            "id": "LINE-001",
            "line_type": "process",
            "page": 1,
            "confidence": 0.95,
        }
    ]

    associations = [
        {
            "source_id": "LINE-001",
            "target_id": "PUMP-001",
            "relation": "connects_from",
        },
        {
            "source_id": "LINE-001",
            "target_id": "TANK-001",
            "relation": "connects_to",
        },
    ]

    node_ids = {"PUMP-001", "TANK-001"}

    edges, unresolved, reasons = build_edges(
        lines, associations, node_ids
    )

    assert len(edges) == 1
    assert edges[0]["source"] == "PUMP-001"
    assert edges[0]["target"] == "TANK-001"
    assert unresolved == []
    assert reasons == {}


def test_missing_target_is_unresolved():
    """A line without a target must not create an edge."""

    lines = [
        {"id": "LINE-002", "line_type": "process"}
    ]

    associations = [
        {
            "source_id": "LINE-002",
            "target_id": "PUMP-001",
            "relation": "connects_from",
        }
    ]

    edges, unresolved, reasons = build_edges(
        lines, associations, {"PUMP-001"}
    )

    assert edges == []
    assert "LINE-002" in unresolved
    assert "Missing target association" in reasons["LINE-002"]


def test_unknown_node_is_unresolved():
    """An association to a missing graph node must not create an edge."""

    lines = [
        {"id": "LINE-003", "line_type": "process"}
    ]

    associations = [
        {
            "source_id": "LINE-003",
            "target_id": "PUMP-001",
            "relation": "connects_from",
        },
        {
            "source_id": "LINE-003",
            "target_id": "TANK-UNKNOWN",
            "relation": "connects_to",
        },
    ]

    edges, unresolved, reasons = build_edges(
        lines, associations, {"PUMP-001"}
    )

    assert edges == []
    assert "LINE-003" in unresolved
    assert any(
        "TANK-UNKNOWN" in reason
        for reason in reasons["LINE-003"]
    )


def test_multiple_targets_do_not_create_fake_edges():
    """Ambiguous endpoints must be reported, not guessed."""

    lines = [
        {"id": "LINE-004", "line_type": "process"}
    ]

    associations = [
        {
            "source_id": "LINE-004",
            "target_id": "PUMP-001",
            "relation": "connects_from",
        },
        {
            "source_id": "LINE-004",
            "target_id": "TANK-001",
            "relation": "connects_to",
        },
        {
            "source_id": "LINE-004",
            "target_id": "TANK-002",
            "relation": "connects_to",
        },
    ]

    node_ids = {"PUMP-001", "TANK-001", "TANK-002"}

    edges, unresolved, reasons = build_edges(
        lines, associations, node_ids
    )

    assert edges == []
    assert "LINE-004" in unresolved
    assert any(
        "Multiple sources or targets" in reason
        for reason in reasons["LINE-004"]
    )


def test_unknown_line_type_is_not_processed():
    """Unknown lines must not be treated as process lines."""

    lines = [
        {"id": "LINE-005", "line_type": "unknown"}
    ]

    associations = [
        {
            "source_id": "LINE-005",
            "target_id": "PUMP-001",
            "relation": "connects_from",
        },
        {
            "source_id": "LINE-005",
            "target_id": "TANK-001",
            "relation": "connects_to",
        },
    ]

    edges, unresolved, reasons = build_edges(
        lines, associations, {"PUMP-001", "TANK-001"}
    )

    assert edges == []
    assert unresolved == []
    assert reasons == {}
