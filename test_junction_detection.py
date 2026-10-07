from m2_topology.junction_detection import detect_junctions


def test_t_junction_is_detected_as_connected():
    lines = [
        {
            "id": "LINE-001",
            "points": [[100, 200], [300, 200]],
            "line_type": "process",
        },
        {
            "id": "LINE-002",
            "points": [[200, 100], [200, 200]],
            "line_type": "process",
        },
    ]

    junctions = detect_junctions(lines)

    assert len(junctions) == 1
    assert junctions[0]["type"] == "T"
    assert junctions[0]["connected"] is True
    assert junctions[0]["crossover"] is False


def test_x_crossover_is_not_automatically_connected():
    lines = [
        {
            "id": "LINE-003",
            "points": [[100, 100], [300, 300]],
            "line_type": "process",
        },
        {
            "id": "LINE-004",
            "points": [[100, 300], [300, 100]],
            "line_type": "process",
        },
    ]

    junctions = detect_junctions(lines)

    assert len(junctions) == 1
    assert junctions[0]["type"] == "X"
    assert junctions[0]["connected"] is False
    assert junctions[0]["crossover"] is True


def test_x_junction_with_explicit_connection_evidence_is_connected():
    lines = [
        {
            "id": "LINE-005",
            "points": [[100, 100], [300, 300]],
            "line_type": "process",
            "connected": True,
        },
        {
            "id": "LINE-006",
            "points": [[100, 300], [300, 100]],
            "line_type": "process",
        },
    ]

    junctions = detect_junctions(lines)

    assert len(junctions) == 1
    assert junctions[0]["type"] == "X"
    assert junctions[0]["connected"] is True
    assert junctions[0]["crossover"] is False


def test_intersection_does_not_create_false_process_connection():
    lines = [
        {
            "id": "LINE-007",
            "points": [[100, 100], [300, 300]],
            "line_type": "process",
        },
        {
            "id": "LINE-008",
            "points": [[100, 300], [300, 100]],
            "line_type": "process",
        },
    ]

    junctions = detect_junctions(lines)

    connected_junctions = [
        junction
        for junction in junctions
        if junction["connected"]
    ]

    assert len(connected_junctions) == 0