import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from m2_topology.graph_builder import (
    build_nodes,
    build_process_connections,
    build_edges,
    create_networkx_graph,
    validate_edges,
    validate_io,
    build_graph,
)


def test_build_nodes_attaches_io_information():
    symbols = [
        {
            "id": "SYM-001",
            "class_name": "tank",
            "tag": "TK-101",
            "bbox": [100, 220, 220, 400],
            "confidence": 0.98,
            "page": 1,
        },
        {
            "id": "SYM-002",
            "class_name": "pump",
            "tag": "P-101",
            "bbox": [300, 270, 380, 350],
            "confidence": 0.97,
            "page": 1,
        },
    ]

    io_list = [
        {
            "tag": "TK-101",
            "type": "LT",
            "description": "Tank level transmitter",
            "loop": "LIC-101",
            "expected_status": "active",
        }
    ]

    nodes = build_nodes(symbols, io_list)

    assert len(nodes) == 2

    tank = nodes[0]

    assert tank["id"] == "SYM-001"
    assert tank["tag"] == "TK-101"
    assert tank["type"] == "tank"
    assert tank["is_io"] is True
    assert tank["io_type"] == "LT"
    assert tank["description"] == "Tank level transmitter"
    assert tank["loop"] == "LIC-101"
    assert tank["preserve"] is True

    pump = nodes[1]

    assert pump["id"] == "SYM-002"
    assert pump["tag"] == "P-101"
    assert pump["is_io"] is False


def test_build_process_connections():
    lines = [
        {
            "id": "LINE-001",
            "line_type": "process",
            "page": 1,
        },
        {
            "id": "LINE-002",
            "line_type": "instrument",
            "page": 1,
        },
    ]

    associations = [
        {
            "source_id": "LINE-001",
            "target_id": "SYM-001",
            "relation": "connects_from",
        },
        {
            "source_id": "LINE-001",
            "target_id": "SYM-002",
            "relation": "connects_to",
        },
        {
            "source_id": "LINE-002",
            "target_id": "SYM-003",
            "relation": "connects_from",
        },
    ]

    connections = build_process_connections(
        lines,
        associations,
    )

    assert connections == {
        "LINE-001": {
            "source": "SYM-001",
            "target": "SYM-002",
        }
    }


def test_build_edges_creates_only_valid_process_edges():
    lines = [
        {
            "id": "LINE-001",
            "line_type": "process",
            "page": 1,
            "confidence": 0.98,
        },
        {
            "id": "LINE-002",
            "line_type": "process",
            "page": 1,
            "confidence": 0.97,
        },
    ]

    associations = [
        {
            "source_id": "LINE-001",
            "target_id": "SYM-001",
            "relation": "connects_from",
        },
        {
            "source_id": "LINE-001",
            "target_id": "SYM-002",
            "relation": "connects_to",
        },
        {
            "source_id": "LINE-002",
            "target_id": "SYM-002",
            "relation": "connects_from",
        },
    ]

    edges, unresolved = build_edges(
        lines,
        associations,
        {"SYM-001", "SYM-002"},
    )

    assert len(edges) == 1

    assert edges[0]["source"] == "SYM-001"
    assert edges[0]["target"] == "SYM-002"
    assert edges[0]["line_id"] == "LINE-001"

    assert unresolved == ["LINE-002"]


def test_create_networkx_graph_is_directed():
    nodes = [
        {
            "id": "SYM-001",
            "tag": "TK-101",
            "type": "tank",
            "preserve": True,
        },
        {
            "id": "SYM-002",
            "tag": "P-101",
            "type": "pump",
            "preserve": True,
        },
    ]

    edges = [
        {
            "id": "EDGE-001",
            "source": "SYM-001",
            "target": "SYM-002",
            "line_type": "process",
        }
    ]

    graph = create_networkx_graph(nodes, edges)

    assert graph.is_directed()
    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1
    assert graph.has_edge("SYM-001", "SYM-002")


def test_validate_edges():
    edges = [
        {
            "id": "EDGE-001",
            "source": "SYM-001",
            "target": "SYM-002",
        },
        {
            "id": "EDGE-002",
            "source": "SYM-001",
            "target": "SYM-999",
        },
    ]

    validated = validate_edges(
        edges,
        {"SYM-001", "SYM-002"},
    )

    assert validated[0]["validated"] is True
    assert validated[1]["validated"] is False


def test_validate_io():
    nodes = [
        {
            "id": "SYM-001",
            "tag": "TK-101",
        },
        {
            "id": "SYM-002",
            "tag": "P-101",
        },
    ]

    io_list = [
        {"tag": "TK-101"},
        {"tag": "P-101"},
        {"tag": "FT-999"},
    ]

    result = validate_io(nodes, io_list)

    assert result["expected_count"] == 3
    assert result["found_count"] == 2
    assert result["missing_count"] == 1
    assert result["missing_tags"] == ["FT-999"]


def test_build_graph_end_to_end():
    symbols = [
        {
            "id": "SYM-001",
            "class_name": "tank",
            "tag": "TK-101",
            "bbox": [100, 220, 220, 400],
            "confidence": 0.98,
            "page": 1,
        },
        {
            "id": "SYM-002",
            "class_name": "pump",
            "tag": "P-101",
            "bbox": [300, 270, 380, 350],
            "confidence": 0.97,
            "page": 1,
        },
    ]

    lines = [
        {
            "id": "LINE-001",
            "points": [[220, 310], [300, 310]],
            "line_type": "process",
            "confidence": 0.98,
            "page": 1,
        }
    ]

    associations = [
        {
            "source_id": "LINE-001",
            "target_id": "SYM-001",
            "relation": "connects_from",
        },
        {
            "source_id": "LINE-001",
            "target_id": "SYM-002",
            "relation": "connects_to",
        },
    ]

    io_list = [
        {"tag": "TK-101", "type": "LT"},
        {"tag": "P-101", "type": "PT"},
    ]

    graph = build_graph(
        symbols=symbols,
        lines=lines,
        associations=associations,
        io_list=io_list,
    )

    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1

    assert graph["edges"][0]["source"] == "SYM-001"
    assert graph["edges"][0]["target"] == "SYM-002"

    assert graph["metadata"]["node_count"] == 2
    assert graph["metadata"]["edge_count"] == 1

    assert graph["metadata"]["io_expected_count"] == 2
    assert graph["metadata"]["io_found_count"] == 2
    assert graph["metadata"]["io_missing_count"] == 0