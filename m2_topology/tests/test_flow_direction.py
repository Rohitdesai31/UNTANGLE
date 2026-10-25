
from m2_topology.flow_direction import determine_flow_direction


def make_graph():
    return {
        "nodes": [
            {"id": "A", "type": "pump"},
            {"id": "B", "type": "tank"},
        ],
        "edges": [
            {"id": "E1", "source": "A", "target": "B",
             "line_id": "L1"}
        ],
    }


def test_forward_arrow():
    graph = make_graph()
    lines = [{"id": "L1", "arrow_direction": "forward"}]

    result = determine_flow_direction(graph, lines)
    edge = result["edges"][0]

    assert edge["flow_direction"] == "forward"
    assert edge["upstream"] == "A"
    assert edge["downstream"] == "B"
    assert edge["direction_source"] == "arrow"


def test_reverse_arrow():
    graph = make_graph()
    lines = [{"id": "L1", "arrow_direction": "reverse"}]

    result = determine_flow_direction(graph, lines)
    edge = result["edges"][0]

    assert edge["flow_direction"] == "reverse"
    assert edge["upstream"] == "B"
    assert edge["downstream"] == "A"


def test_missing_arrow():
    graph = make_graph()

    result = determine_flow_direction(graph, [])
    edge = result["edges"][0]

    assert edge["flow_direction"] == "unknown"
    assert edge["upstream"] is None
    assert edge["downstream"] is None
    assert edge["direction_source"] == "insufficient_evidence"


def test_invalid_endpoint():
    graph = make_graph()
    graph["edges"][0]["target"] = "MISSING"

    result = determine_flow_direction(
        graph,
        [{"id": "L1", "arrow_direction": "forward"}],
    )
    edge = result["edges"][0]

    assert edge["flow_direction"] == "unknown"
    assert edge["upstream"] is None
    assert edge["downstream"] is None
    assert edge["direction_source"] == "invalid_endpoint"


def test_invalid_arrow_value():
    graph = make_graph()
    lines = [{"id": "L1", "arrow_direction": "left"}]

    result = determine_flow_direction(graph, lines)
    edge = result["edges"][0]

    assert edge["flow_direction"] == "unknown"
    assert edge["direction_source"] == "insufficient_evidence"
