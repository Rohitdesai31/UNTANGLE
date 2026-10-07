"""
UNTANGLE - Phase 4
Step 5: SVG Generation

Generates the simplified process sketch.

Rules:
- Main process equipment is visible by default.
- Instrumentation remains preserved in graph_simple.json.
- Instrumentation is hidden from the default sketch.
- Process connections are drawn using calculated routes.
- Flow direction is shown using arrows.
- Tags and equipment descriptions are shown.
- SVG XML values are escaped safely.
"""


# ============================================================
# XML SAFETY
# ============================================================

def escape_xml(value):
    """Escape text before placing it inside SVG/XML."""

    value = str(value)

    return (
        value
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


# ============================================================
# NODE CLASSIFICATION
# ============================================================

INSTRUMENT_CLASSES = {
    "flow_transmitter",
    "flow_indicator_controller",
    "flow_indicator",
    "pressure_transmitter",
    "pressure_indicator",
    "temperature_transmitter",
    "temperature_indicator",
    "level_transmitter",
    "level_indicator",
    "control_valve",
    "flow_control_valve",
    "pressure_control_valve",
    "temperature_control_valve",
    "level_control_valve",
}


def get_node_class(node):
    """
    Read the node class from the graph.

    M1/M2 data uses class_name.
    type is supported as a fallback.
    """

    return (
        node.get("class_name")
        or node.get("type")
        or ""
    ).lower()


def is_instrument(node):
    """Return True when the node represents instrumentation."""

    return get_node_class(node) in INSTRUMENT_CLASSES


# ============================================================
# SVG GENERATION
# ============================================================

def generate_svg(graph, output_path):
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    # --------------------------------------------------------
    # Determine canvas size from actual layout positions
    # --------------------------------------------------------

    layout_positions = []

    for node in nodes:

        layout = node.get("layout", {})

        if "x" in layout and "y" in layout:
            layout_positions.append(
                (
                    layout["x"],
                    layout["y"],
                )
            )

    if layout_positions:

        max_x = max(
            position[0]
            for position in layout_positions
        )

        max_y = max(
            position[1]
            for position in layout_positions
        )

        width = max(
            1200,
            max_x + 250
        )

        height = max(
            600,
            max_y + 180
        )

    else:

        width = 1200
        height = 600

    # --------------------------------------------------------
    # SVG header
    # --------------------------------------------------------

    svg = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',

        "<defs>",

        '<marker id="arrow" '
        'markerWidth="10" '
        'markerHeight="10" '
        'refX="9" '
        'refY="3" '
        'orient="auto" '
        'markerUnits="strokeWidth">',

        '<path d="M0,0 L0,6 L9,3 z" '
        'fill="black"/>',

        "</marker>",

        "</defs>",
    ]

    # ========================================================
    # 1. DRAW PROCESS CONNECTIONS
    # ========================================================

    for edge in edges:

        route = edge.get("route", [])

        if len(route) < 2:
            continue

        points = " ".join(
            f"{point[0]},{point[1]}"
            for point in route
        )

        svg.append(
            f'<polyline '
            f'points="{points}" '
            f'fill="none" '
            f'stroke="black" '
            f'stroke-width="2" '
            f'marker-end="url(#arrow)"/>'
        )

    # ========================================================
    # 2. DRAW MAIN PROCESS EQUIPMENT
    # ========================================================

    for node in nodes:

        # Instruments are preserved in the graph but hidden
        # from the default simplified sketch.
        if is_instrument(node):
            continue

        layout = node.get("layout", {})

        if (
            "x" not in layout
            or "y" not in layout
        ):
            continue

        x = layout["x"]
        y = layout["y"]

        tag = escape_xml(
            node.get("tag")
            or node.get("id")
        )

        node_class = escape_xml(
            get_node_class(node)
            or "equipment"
        )

        # ----------------------------------------------------
        # Equipment box
        # ----------------------------------------------------

        svg.append(
            f'<rect '
            f'x="{x - 55}" '
            f'y="{y - 30}" '
            f'width="110" '
            f'height="60" '
            f'fill="white" '
            f'stroke="black" '
            f'stroke-width="2"/>'
        )

        # ----------------------------------------------------
        # Equipment tag
        # ----------------------------------------------------

        svg.append(
            f'<text '
            f'x="{x}" '
            f'y="{y}" '
            f'text-anchor="middle" '
            f'font-size="14">'
            f'{tag}'
            f'</text>'
        )

        # ----------------------------------------------------
        # Equipment class
        # ----------------------------------------------------

        svg.append(
            f'<text '
            f'x="{x}" '
            f'y="{y + 20}" '
            f'text-anchor="middle" '
            f'font-size="10">'
            f'{node_class}'
            f'</text>'
        )

    # ========================================================
    # 3. CLOSE SVG
    # ========================================================

    svg.append("</svg>")

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "\n".join(svg)
        )

    return output_path


# ============================================================
# MAPPING
# ============================================================

def create_mapping(graph):
    """
    Create mapping between simplified sketch elements
    and their original graph elements.
    """

    mapping = {
        "nodes": {},
        "edges": {},
    }

    # --------------------------------------------------------
    # Node mapping
    # --------------------------------------------------------

    for node in graph.get("nodes", []):

        tag = (
            node.get("tag")
            or node["id"]
        )

        mapping["nodes"][tag] = {
            "original_id": node.get("id"),
            "global_id": node.get("global_id"),
            "page": node.get("page"),
            "type": get_node_class(node),
            "visible_by_default": not is_instrument(node),
            "preserve": node.get("preserve", False),
        }

    # --------------------------------------------------------
    # Edge mapping
    # --------------------------------------------------------

    for edge in graph.get("edges", []):

        edge_id = edge.get("id")

        if not edge_id:
            continue

        mapping["edges"][edge_id] = {
            "source": edge.get("source"),
            "target": edge.get("target"),
            "line_id": edge.get("line_id"),
            "flow_direction": edge.get(
                "flow_direction"
            ),
            "route": edge.get("route", []),
        }

    return mapping