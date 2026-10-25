
from m2_topology.junction_detection import detect_junctions


def test_t_junction():
    lines = [
        {"id": "L1", "points": [[0, 5], [10, 5]]},
        {"id": "L2", "points": [[5, 5], [5, 10]]},
    ]

    result = detect_junctions(lines)

    assert len(result) == 1
    assert result[0]["type"] == "T"
    assert result[0]["connected"] is True


def test_x_crossing_without_evidence():
    lines = [
        {"id": "L1", "points": [[0, 0], [10, 10]]},
        {"id": "L2", "points": [[0, 10], [10, 0]]},
    ]

    result = detect_junctions(lines)

    assert len(result) == 1
    assert result[0]["type"] == "X"
    assert result[0]["connected"] is False
    assert result[0]["crossover"] is True


def test_x_crossing_with_evidence():
    lines = [
        {"id": "L1", "points": [[0, 0], [10, 10]],
         "connected": True},
        {"id": "L2", "points": [[0, 10], [10, 0]]},
    ]

    result = detect_junctions(lines)

    assert len(result) == 1
    assert result[0]["connected"] is True


def test_no_intersection():
    lines = [
        {"id": "L1", "points": [[0, 0], [2, 0]]},
        {"id": "L2", "points": [[5, 5], [8, 5]]},
    ]

    assert detect_junctions(lines) == []


def test_bent_line_intersection():
    lines = [
        {"id": "L1", "points": [[0, 0], [5, 0], [5, 10]]},
        {"id": "L2", "points": [[3, 3], [7, 3]]},
    ]

    result = detect_junctions(lines)

    assert len(result) == 1
    assert result[0]["point"] == [5.0, 3.0]
    assert result[0]["type"] == "X"
    assert result[0]["connected"] is False
