from m2_topology.flow_direction import determine_flow_direction


def test_forward_flow():
    graph = {
        "nodes": [
            {"id": "A", "x": 100, "y": 100},
            {"id": "B", "x": 200, "y": 100},
        ],
        "edges": [
            {"id": "E1", "source": "A", "target": "B"}
        ],
    }

    result = determine_flow_direction(graph)

    edge = result["edges"][0]

    assert edge["flow_direction"] == "forward"
    assert edge["upstream"] == "A"
    assert edge["downstream"] == "B"


def test_reverse_flow():
    graph = {
        "nodes": [
            {"id": "A", "x": 200, "y": 100},
            {"id": "B", "x": 100, "y": 100},
        ],
        "edges": [
            {"id": "E1", "source": "A", "target": "B"}
        ],
    }

    result = determine_flow_direction(graph)

    edge = result["edges"][0]

    assert edge["flow_direction"] == "reverse"
    assert edge["upstream"] == "B"
    assert edge["downstream"] == "A"


def test_vertical_flow():
    graph = {
        "nodes": [
            {"id": "A", "x": 100, "y": 100},
            {"id": "B", "x": 100, "y": 200},
        ],
        "edges": [
            {"id": "E1", "source": "A", "target": "B"}
        ],
    }

    result = determine_flow_direction(graph)

    edge = result["edges"][0]

    assert edge["flow_direction"] == "forward"
    assert edge["upstream"] == "A"
    assert edge["downstream"] == "B"

def test_branch_flow():
    graph = {
        "nodes": [
            {"id": "A", "x": 100, "y": 100},
            {"id": "B", "x": 200, "y": 100},
            {"id": "C", "x": 300, "y": 50},
            {"id": "D", "x": 300, "y": 150},
        ],
        "edges": [
            {"id": "E1", "source": "A", "target": "B"},
            {"id": "E2", "source": "B", "target": "C"},
            {"id": "E3", "source": "B", "target": "D"},
        ],
    }

    result = determine_flow_direction(graph)

    assert result["edges"][0]["upstream"] == "A"
    assert result["edges"][0]["downstream"] == "B"

    assert result["edges"][1]["upstream"] == "B"
    assert result["edges"][1]["downstream"] == "C"

    assert result["edges"][2]["upstream"] == "B"
    assert result["edges"][2]["downstream"] == "D"


def test_merge_flow():
    graph = {
        "nodes": [
            {"id": "A", "x": 100, "y": 50},
            {"id": "B", "x": 100, "y": 150},
            {"id": "C", "x": 200, "y": 100},
        ],
        "edges": [
            {"id": "E1", "source": "A", "target": "C"},
            {"id": "E2", "source": "B", "target": "C"},
        ],
    }

    result = determine_flow_direction(graph)

    assert result["edges"][0]["upstream"] == "A"
    assert result["edges"][0]["downstream"] == "C"

    assert result["edges"][1]["upstream"] == "B"
    assert result["edges"][1]["downstream"] == "C"


def test_arrow_direction():
    graph = {
        "nodes": [
            {"id": "A", "x": 100, "y": 100},
            {"id": "B", "x": 200, "y": 100},
        ],
        "edges": [
            {
                "id": "E1",
                "source": "A",
                "target": "B",
                "line_id": "L1",
            }
        ],
    }

    lines = [
        {
            "id": "L1",
            "points": [[100, 100], [200, 100]],
            "arrow_direction": "reverse",
        }
    ]

    result = determine_flow_direction(graph, lines)

    assert result["edges"][0]["flow_direction"] == "reverse"
    assert result["edges"][0]["upstream"] == "B"
    assert result["edges"][0]["downstream"] == "A"
    assert result["edges"][0]["direction_source"] == "arrow"

def test_duty_standby_detection():
    from m2_topology.pump_patterns import detect_pump_patterns

    graph = {
        "nodes": [
            {"id": "T1", "tag": "TK-101", "type": "tank"},
            {"id": "P1", "tag": "P-101A", "type": "pump"},
            {"id": "P2", "tag": "P-101B", "type": "pump"},
            {"id": "V1", "tag": "V-101", "type": "valve"},
        ],
        "edges": [
            {"id": "E1", "source": "T1", "target": "P1"},
            {"id": "E2", "source": "T1", "target": "P2"},
            {"id": "E3", "source": "P1", "target": "V1"},
            {"id": "E4", "source": "P2", "target": "V1"},
        ],
    }

    result = detect_pump_patterns(graph)

    groups = result

    assert len(groups) == 1

    group = groups[0]

    assert set(group["pump_ids"]) == {"P1", "P2"}
    assert group["type"] == "duty_standby"

def test_multipage_topology():
    from m2_topology.multipage import build_multipage_topology

    pages = [
        {"page": 1, "next_page": 2},
        {"page": 2, "previous_page": 1, "next_page": 3},
        {"page": 3, "previous_page": 2},
    ]

    symbols = [
        {"id": "SYM-001", "tag": "P-101", "type": "pump", "page": 1},
        {"id": "SYM-001", "tag": "P-101", "type": "pump", "page": 2},
        {"id": "SYM-002", "tag": "R-101", "type": "reactor", "page": 3},
    ]

    lines = [
        {
            "id": "LINE-001",
            "page": 1,
            "source": "SYM-001",
            "target": "SYM-001",
            "continuation": True,
        },
        {
            "id": "LINE-002",
            "page": 2,
            "source": "SYM-001",
            "target": "SYM-002",
            "continues_to": 3,
        },
    ]

    result = build_multipage_topology(
        pages,
        symbols,
        lines
    )

    # Page references
    assert len(result["page_references"]) >= 2

    # Global IDs
    assert result["symbols"][0]["global_id"] == "P1-SYM-SYM-001"
    assert result["symbols"][1]["global_id"] == "P2-SYM-SYM-001"

    # Duplicate tags
    assert "P-101" in result["duplicate_tags"]

    # Continuation lines
    assert len(result["continuation_lines"]) >= 1

    # Global topology
    assert result["global_topology"] is True