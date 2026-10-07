import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from m3_simplify.simplify import simplify_graph


def test_simplify_keeps_preserved_nodes():
    graph = {
        "nodes": [
            {
                "id": "N001",
                "tag": "TK-101",
                "type": "tank",
                "preserve": True,
            },
            {
                "id": "N002",
                "tag": "P-101",
                "type": "pump",
                "preserve": True,
            },
            {
                "id": "N003",
                "tag": "TEMP-DETAIL",
                "type": "unnecessary_detail",
                "preserve": False,
            },
        ],
        "edges": [],
    }

    result = simplify_graph(graph)

    assert len(result["nodes"]) == 2

    node_ids = {
        node["id"]
        for node in result["nodes"]
    }

    assert node_ids == {"N001", "N002"}

    assert len(result["simplification_log"]) == 1
    assert result["simplification_log"][0]["type"] == "node"
    assert result["simplification_log"][0]["node"] == "N003"


def test_simplify_preserves_valid_connections():
    graph = {
        "nodes": [
            {
                "id": "N001",
                "tag": "TK-101",
                "type": "tank",
                "preserve": True,
            },
            {
                "id": "N002",
                "tag": "P-101",
                "type": "pump",
                "preserve": True,
            },
        ],
        "edges": [
            {
                "id": "E001",
                "source": "N001",
                "target": "N002",
                "preserve": True,
                "flow_direction": "forward",
            }
        ],
    }

    result = simplify_graph(graph)

    assert len(result["edges"]) == 1

    edge = result["edges"][0]

    assert edge["id"] == "E001"
    assert edge["source"] == "N001"
    assert edge["target"] == "N002"
    assert edge["flow_direction"] == "forward"


def test_simplify_removes_connection_with_unpreserved_endpoint():
    graph = {
        "nodes": [
            {
                "id": "N001",
                "tag": "TK-101",
                "type": "tank",
                "preserve": True,
            },
            {
                "id": "N002",
                "tag": "DETAIL-001",
                "type": "detail",
                "preserve": False,
            },
        ],
        "edges": [
            {
                "id": "E001",
                "source": "N001",
                "target": "N002",
                "preserve": True,
            }
        ],
    }

    result = simplify_graph(graph)

    assert len(result["edges"]) == 0

    assert len(result["simplification_log"]) == 2

    edge_logs = [
        item
        for item in result["simplification_log"]
        if item["type"] == "edge"
    ]

    assert len(edge_logs) == 1
    assert edge_logs[0]["edge"] == "E001"


def test_simplify_respects_edge_preserve_flag():
    graph = {
        "nodes": [
            {
                "id": "N001",
                "tag": "TK-101",
                "preserve": True,
            },
            {
                "id": "N002",
                "tag": "P-101",
                "preserve": True,
            },
        ],
        "edges": [
            {
                "id": "E001",
                "source": "N001",
                "target": "N002",
                "preserve": False,
            }
        ],
    }

    result = simplify_graph(graph)

    assert len(result["edges"]) == 0

    edge_logs = [
        item
        for item in result["simplification_log"]
        if item["type"] == "edge"
    ]

    assert len(edge_logs) == 1
    assert edge_logs[0]["edge"] == "E001"


def test_simplify_preserves_pump_patterns_and_junctions():
    graph = {
        "nodes": [
            {
                "id": "N001",
                "tag": "TK-101",
                "preserve": True,
            },
            {
                "id": "N002",
                "tag": "P-101",
                "preserve": True,
            },
        ],
        "edges": [],
        "pump_patterns": [
            {
                "type": "duty_standby",
                "nodes": ["N002"],
            }
        ],
        "junctions": [
            {
                "id": "J001",
                "type": "T",
                "connected": True,
            }
        ],
    }

    result = simplify_graph(graph)

    assert "pump_patterns" in result
    assert "junctions" in result

    assert result["pump_patterns"][0]["type"] == "duty_standby"
    assert result["junctions"][0]["id"] == "J001"


def test_simplify_metadata_is_correct():
    graph = {
        "nodes": [
            {
                "id": "N001",
                "preserve": True,
            },
            {
                "id": "N002",
                "preserve": False,
            },
        ],
        "edges": [
            {
                "id": "E001",
                "source": "N001",
                "target": "N002",
                "preserve": False,
            }
        ],
        "metadata": {
            "graph_type": "directed",
        },
    }

    result = simplify_graph(graph)

    assert result["metadata"]["source"] == "graph_full.json"
    assert result["metadata"]["graph_type"] == "directed"

    assert result["metadata"]["node_count"] == 1
    assert result["metadata"]["edge_count"] == 0

    assert result["metadata"]["original_node_count"] == 2
    assert result["metadata"]["original_edge_count"] == 1