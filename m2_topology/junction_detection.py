
from __future__ import annotations

from math import hypot
from typing import Any


EPSILON = 1e-6


def _point_equal(p1, p2, tolerance=EPSILON):
    return (
        abs(p1[0] - p2[0]) <= tolerance
        and abs(p1[1] - p2[1]) <= tolerance
    )

def _get_segments(line):
    points = line.get("points", [])
    return [
        (points[i], points[i + 1])
        for i in range(len(points) - 1)
    ]


def _orientation(a, b, c):
    value = (
        (b[1] - a[1]) * (c[0] - b[0])
        - (b[0] - a[0]) * (c[1] - b[1])
    )

    if abs(value) <= EPSILON:
        return 0

    return 1 if value > 0 else 2


def _on_segment(a, b, c):
    return (
        min(a[0], c[0]) - EPSILON <= b[0] <= max(a[0], c[0]) + EPSILON
        and min(a[1], c[1]) - EPSILON <= b[1] <= max(a[1], c[1]) + EPSILON
    )


def _segment_intersection(p1, p2, q1, q2):
    """
    Returns the intersection point when two line segments intersect.

    Returns None when they do not intersect.
    """

    o1 = _orientation(p1, p2, q1)
    o2 = _orientation(p1, p2, q2)
    o3 = _orientation(q1, q2, p1)
    o4 = _orientation(q1, q2, p2)

    # Proper intersection
    if o1 != o2 and o3 != o4:
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = q1
        x4, y4 = q2

        denominator = (
            (x1 - x2) * (y3 - y4)
            - (y1 - y2) * (x3 - x4)
        )

        if abs(denominator) <= EPSILON:
            return None

        px = (
            (x1 * y2 - y1 * x2) * (x3 - x4)
            - (x1 - x2) * (x3 * y4 - y3 * x4)
        ) / denominator

        py = (
            (x1 * y2 - y1 * x2) * (y3 - y4)
            - (y1 - y2) * (x3 * y4 - y3 * x4)
        ) / denominator

        return [px, py]

    # Collinear cases
    if o1 == 0 and _on_segment(p1, q1, p2):
        return list(q1)

    if o2 == 0 and _on_segment(p1, q2, p2):
        return list(q2)

    if o3 == 0 and _on_segment(q1, p1, q2):
        return list(p1)

    if o4 == 0 and _on_segment(q1, p2, q2):
        return list(p2)

    return None


def _is_endpoint(point, line):
    points = line.get("points", [])

    if len(points) < 2:
        return False

    return (
        _point_equal(point, points[0])
        or _point_equal(point, points[-1])
    )


def _has_explicit_connection_evidence(line1, line2):
    """
    Geometry alone must NOT turn a visual X-crossing into a connection.

    Explicit connection evidence can be supplied by upstream processing
    using fields such as:
      connected
      junction
      connection
      connection_point
      dot
    """

    evidence_keys = (
        "connected",
        "junction",
        "connection",
        "connection_point",
        "dot",
    )

    for key in evidence_keys:
        if line1.get(key) is True or line2.get(key) is True:
            return True

    return False



def detect_junctions(lines):
    """
    Detect intersections between process lines, including bent lines.

    T-junctions are treated as connected.
    X-crossings are not connected unless explicit evidence exists.
    Intersections alone must never create graph edges.
    """

    process_lines = [
        line
        for line in lines
        if line.get("line_type", "process") == "process"
        and len(line.get("points", [])) >= 2
        and line.get("id") is not None
    ]

    junctions = []
    seen = set()

    for i in range(len(process_lines)):
        for j in range(i + 1, len(process_lines)):
            line1 = process_lines[i]
            line2 = process_lines[j]

            segments1 = _get_segments(line1)
            segments2 = _get_segments(line2)

            for p1, p2 in segments1:
                for q1, q2 in segments2:
                    intersection = _segment_intersection(
                        p1, p2, q1, q2
                    )

                    if intersection is None:
                        continue

                    # Determine whether the intersection is an
                    # endpoint of each complete line.
                    line1_endpoint = _is_endpoint(intersection, line1)
                    line2_endpoint = _is_endpoint(intersection, line2)

                    # Avoid duplicate reports at the same point
                    # when consecutive segments meet there.
                    point_key = (
                        round(intersection[0], 6),
                        round(intersection[1], 6),
                    )
                    pair_key = (
                        line1["id"],
                        line2["id"],
                        point_key,
                    )

                    if pair_key in seen:
                        continue

                    seen.add(pair_key)

                    if line1_endpoint != line2_endpoint:
                        junction_type = "T"
                        connected = True

                    elif not line1_endpoint and not line2_endpoint:
                        junction_type = "X"
                        connected = _has_explicit_connection_evidence(
                            line1, line2
                        )

                    else:
                        junction_type = "shared_endpoint"
                        connected = True

                    junctions.append(
                        {
                            "id": f"JUNCTION-{len(junctions) + 1:03d}",
                            "type": junction_type,
                            "point": intersection,
                            "line_ids": [
                                line1["id"],
                                line2["id"],
                            ],
                            "connected": connected,
                            "crossover": (
                                junction_type == "X"
                                and not connected
                            ),
                        }
                    )

    return junctions
