from m2_topology.pump_patterns import detect_pump_patterns


def test_parallel_pumps_are_detected():
    graph = {
        "nodes": [
            {
                "id": "TK-101",
                "type": "tank",
                "tag": "TK-101",
            },
            {
                "id": "P-101A",
                "type": "pump",
                "tag": "P-101A",
            },
            {
                "id": "P-101B",
                "type": "pump",
                "tag": "P-101B",
            },
            {
                "id": "R-101",
                "type": "reactor",
                "tag": "R-101",
            },
        ],
        "edges": [
            {
                "source": "TK-101",
                "target": "P-101A",
                "upstream": "TK-101",
                "downstream": "P-101A",
            },
            {
                "source": "TK-101",
                "target": "P-101B",
                "upstream": "TK-101",
                "downstream": "P-101B",
            },
            {
                "source": "P-101A",
                "target": "R-101",
                "upstream": "P-101A",
                "downstream": "R-101",
            },
            {
                "source": "P-101B",
                "target": "R-101",
                "upstream": "P-101B",
                "downstream": "R-101",
            },
        ],
    }

    patterns = detect_pump_patterns(graph)

    assert len(patterns) >= 1

    parallel_pumps = [
        pattern
        for pattern in patterns
        if set(pattern["pump_tags"]) == {"P-101A", "P-101B"}
    ]

    assert len(parallel_pumps) == 1

    pattern = parallel_pumps[0]

    assert pattern["type"] == "duty_standby"
    assert set(pattern["pump_ids"]) == {"P-101A", "P-101B"}