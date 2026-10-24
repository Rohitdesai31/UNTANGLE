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

def test_simplify_bridges_hidden_intermediate_node():
    graph = {
        "nodes": [
            {
                "id": "A",
                "tag": "TK-101",
                "type": "tank",
                "preserve": True,
            },
            {
                "id": "H",
                "tag": "XV-DETAIL",
                "type": "valve",
                "preserve": False,
            },
            {
                "id": "B",
                "tag": "P-101",
                "type": "pump",
                "preserve": True,
            },
        ],
        "edges": [
            {
                "id": "E001",
                "source": "A",
                "target": "H",
                "line_id": "L001",
                "preserve": True,
            },
            {
                "id": "E002",
                "source": "H",
                "target": "B",
                "line_id": "L002",
                "preserve": True,
            },
        ],
    }

    result = simplify_graph(graph)

    assert len(result["nodes"]) == 2
    assert len(result["edges"]) == 1

    edge = result["edges"][0]

    assert edge["source"] == "A"
    assert edge["target"] == "B"
    assert edge["generated_by"] == "m3_connectivity_bridge"

    assert set(edge["original_edge_ids"]) == {
        "E001",
        "E002",
    }


def test_simplify_bridges_multiple_hidden_nodes():
    graph = {
        "nodes": [
            {
                "id": "A",
                "preserve": True,
            },
            {
                "id": "H1",
                "preserve": False,
            },
            {
                "id": "H2",
                "preserve": False,
            },
            {
                "id": "B",
                "preserve": True,
            },
        ],
        "edges": [
            {
                "id": "E001",
                "source": "A",
                "target": "H1",
                "preserve": True,
            },
            {
                "id": "E002",
                "source": "H1",
                "target": "H2",
                "preserve": True,
            },
            {
                "id": "E003",
                "source": "H2",
                "target": "B",
                "preserve": True,
            },
        ],
    }

    result = simplify_graph(graph)

    assert len(result["nodes"]) == 2
    assert len(result["edges"]) == 1

    edge = result["edges"][0]

    assert edge["source"] == "A"
    assert edge["target"] == "B"

    assert set(edge["original_edge_ids"]) == {
        "E001",
        "E002",
        "E003",
    }


def test_simplify_does_not_collapse_hidden_branch():
    graph = {
        "nodes": [
            {
                "id": "A",
                "preserve": True,
            },
            {
                "id": "H",
                "preserve": False,
            },
            {
                "id": "B",
                "preserve": True,
            },
            {
                "id": "C",
                "preserve": True,
            },
        ],
        "edges": [
            {
                "id": "E001",
                "source": "A",
                "target": "H",
                "preserve": True,
            },
            {
                "id": "E002",
                "source": "H",
                "target": "B",
                "preserve": True,
            },
            {
                "id": "E003",
                "source": "H",
                "target": "C",
                "preserve": True,
            },
        ],
    }

    result = simplify_graph(graph)

    assert len(result["edges"]) == 0

    assert result["metadata"]["connectivity_bridges"] == 0

def test_simplify_bridge_preserves_flow_direction():
    graph = {
        "nodes": [
            {"id": "A", "preserve": True},
            {"id": "H", "preserve": False},
            {"id": "B", "preserve": True},
        ],
        "edges": [
            {
                "id": "E001",
                "source": "A",
                "target": "H",
                "preserve": True,
                "flow_direction": "forward",
            },
            {
                "id": "E002",
                "source": "H",
                "target": "B",
                "preserve": True,
                "flow_direction": "forward",
            },
        ],
    }

    result = simplify_graph(graph)

    assert len(result["edges"]) == 1
    assert result["edges"][0]["source"] == "A"
    assert result["edges"][0]["target"] == "B"
    assert result["edges"][0]["flow_direction"] == "forward"


def test_simplify_bridge_unknown_for_inconsistent_flow_direction():
    graph = {
        "nodes": [
            {"id": "A", "preserve": True},
            {"id": "H", "preserve": False},
            {"id": "B", "preserve": True},
        ],
        "edges": [
            {
                "id": "E001",
                "source": "A",
                "target": "H",
                "preserve": True,
                "flow_direction": "forward",
            },
            {
                "id": "E002",
                "source": "H",
                "target": "B",
                "preserve": True,
                "flow_direction": "reverse",
            },
        ],
    }

    result = simplify_graph(graph)

    assert len(result["edges"]) == 1
    assert result["edges"][0]["flow_direction"] == "unknown"

def test_m2_graph_is_compatible_with_m3_simplification():
    graph = {
        "nodes": [
            {
                "id": "P-101",
                "tag": "P-101",
                "type": "pump",
                "is_io": False,
                "preserve": True,
            },
            {
                "id": "FT-101",
                "tag": "FT-101",
                "type": "flow_transmitter",
                "is_io": True,
                "preserve": True,
            },
            {
                "id": "HIDDEN-101",
                "tag": None,
                "type": "process_line",
                "is_io": False,
                "preserve": False,
            },
            {
                "id": "R-101",
                "tag": "R-101",
                "type": "reactor",
                "is_io": False,
                "preserve": True,
            },
        ],
        "edges": [
            {
                "id": "EDGE-001",
                "source": "P-101",
                "target": "HIDDEN-101",
                "line_id": "L-101",
                "line_type": "process",
                "flow_direction": "forward",
                "preserve": True,
            },
            {
                "id": "EDGE-002",
                "source": "HIDDEN-101",
                "target": "FT-101",
                "line_id": "L-102",
                "line_type": "process",
                "flow_direction": "forward",
                "preserve": True,
            },
            {
                "id": "EDGE-003",
                "source": "FT-101",
                "target": "R-101",
                "line_id": "L-103",
                "line_type": "process",
                "flow_direction": "forward",
                "preserve": True,
            },
        ],
    }

    result = simplify_graph(graph)

    node_ids = {
        node["id"]
        for node in result["nodes"]
    }

    assert node_ids == {
        "P-101",
        "FT-101",
        "R-101",
    }

    assert len(result["edges"]) == 2

    bridge = next(
        edge
        for edge in result["edges"]
        if edge.get("generated_by") == "m3_connectivity_bridge"
    )

    assert bridge["source"] == "P-101"
    assert bridge["target"] == "FT-101"
    assert bridge["flow_direction"] == "forward"
    assert bridge["original_edge_ids"] == [
        "EDGE-001",
        "EDGE-002",
    ]

def test_simplify_does_not_bridge_hidden_branch():
    graph = {
        "nodes": [
            {"id": "A", "preserve": True},
            {"id": "H", "preserve": False},
            {"id": "B", "preserve": True},
            {"id": "C", "preserve": True},
        ],
        "edges": [
            {
                "id": "E001",
                "source": "A",
                "target": "H",
                "preserve": True,
                "flow_direction": "forward",
            },
            {
                "id": "E002",
                "source": "H",
                "target": "B",
                "preserve": True,
                "flow_direction": "forward",
            },
            {
                "id": "E003",
                "source": "H",
                "target": "C",
                "preserve": True,
                "flow_direction": "forward",
            },
        ],
    }

    result = simplify_graph(graph)

    bridges = [
        edge
        for edge in result["edges"]
        if edge.get("generated_by") == "m3_connectivity_bridge"
    ]

    assert len(bridges) == 0