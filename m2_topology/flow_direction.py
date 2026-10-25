"""
UNTANGLE - Flow Direction

Determine upstream/downstream direction for process edges
using the detected process geometry.

Harshada responsibility:
- Flow direction
- Upstream / downstream
- Preserve branch and merge direction information
"""

from math import hypot


def get_node_center(node):
    """
    Return the center point of a node.

    Priority:
    1. Explicit x/y
    2. Bounding box center
    """

    x = node.get("x")
    y = node.get("y")

    if x is not None and y is not None:
        return float(x), float(y)

    bbox = node.get("bbox")

    if bbox and len(bbox) >= 4:
        x1, y1, x2, y2 = bbox[:4]

        return (
            (float(x1) + float(x2)) / 2,
            (float(y1) + float(y2)) / 2,
        )

    if bbox and len(bbox) >= 2:
        return float(bbox[0]), float(bbox[1])

    return None, None


def get_line_direction(line):
    """
    Determine the geometric direction of a process line.

    Returns:
        forward
        reverse
        unknown
    """

    points = line.get("points", [])

    if len(points) < 2:
        return "unknown"

    start = points[0]
    end = points[-1]

    if len(start) < 2 or len(end) < 2:
        return "unknown"

    x1, y1 = float(start[0]), float(start[1])
    x2, y2 = float(end[0]), float(end[1])

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return "unknown"

    # Primary process-flow convention:
    # left -> right
    if abs(dx) >= abs(dy):
        if dx > 0:
            return "forward"
        return "reverse"

    # For mostly vertical lines, use vertical direction.
    if dy > 0:
        return "forward"

    return "reverse"


def get_edge_line(edge, lines_by_id):
    """
    Return the original line information for an edge.
    """

    line_id = edge.get("line_id")

    if not line_id:
        return None

    return lines_by_id.get(line_id)


def get_arrow_direction(line):
    """
    Return explicit arrow direction if detected.
    """

    if not line:
        return None

    arrow_direction = line.get("arrow_direction")

    if arrow_direction in {"forward", "reverse"}:
        return arrow_direction

    return None

def determine_flow_direction(graph, lines=None):
    """
    Add flow-direction information to every process edge.
    Use explicit arrow direction only; do not guess from geometry.
    """

    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    node_map = {
        node.get("id"): node
        for node in nodes
        if node.get("id")
    }

    lines_by_id = {
        line.get("id"): line
        for line in (lines or [])
        if line.get("id")
    }

    for edge in edges:
        source_id = edge.get("source")
        target_id = edge.get("target")

        source = node_map.get(source_id)
        target = node_map.get(target_id)

        if not source or not target:
            edge["flow_direction"] = "unknown"
            edge["upstream"] = None
            edge["downstream"] = None
            edge["direction_source"] = "invalid_endpoint"
            continue

        line = get_edge_line(edge, lines_by_id)
        arrow_direction = get_arrow_direction(line)

        if arrow_direction == "forward":
            edge["flow_direction"] = "forward"
            edge["upstream"] = source_id
            edge["downstream"] = target_id
            edge["direction_source"] = "arrow"

        elif arrow_direction == "reverse":
            edge["flow_direction"] = "reverse"
            edge["upstream"] = target_id
            edge["downstream"] = source_id
            edge["direction_source"] = "arrow"

        else:
            edge["flow_direction"] = "unknown"
            edge["upstream"] = None
            edge["downstream"] = None
            edge["direction_source"] = "insufficient_evidence"

    return graph